from pathlib import Path

from verity_api import db
from verity_api.analysis import build_analysis_pack
from verity_api.db import (
    get_report_artifact,
    get_report,
    list_evidence,
    persist_llm_workflow_result,
)
from verity_api.qa import run_qa_gate
from verity_api.report_workflow import run_report_writer


def _completed_writer(output: dict) -> dict:
    return {
        "status": "completed",
        "reason": "completed",
        "expert_id": "report_writer",
        "provider_status": {"provider": "test", "model": "test-model", "model_tier": "strong"},
        "is_real_llm_execution": True,
        "mock_fallback_used": False,
        "output": output,
        "error": None,
        "trace_step": {"id": "trace-report-writer"},
    }


def _persist_pack_and_qa(monkeypatch, tmp_path: Path, *, verdict: str) -> tuple[dict, dict]:
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "verity.db")
    evidence = list_evidence("mock-001")[:1]
    claims = [
        {
            "id": "claim_writer_001",
            "text": "产品定位证据已被绑定。",
            "status": "supported",
            "strength": "weak",
            "dimension": "产品定位",
            "evidence_ids": [evidence[0]["id"]],
            "risk_note": "",
        }
    ]
    pack = build_analysis_pack(
        report_id="mock-001",
        research_goal="验证报告撰写门控",
        dimensions=["产品定位"],
        claims=claims,
        evidence_items=evidence,
    )
    qa_result = run_qa_gate(pack)
    qa_result["verdict"] = verdict
    persist_llm_workflow_result(
        report_id="mock-001",
        title="报告撰写门控测试",
        research_goal="验证报告撰写门控",
        competitors=["Gamma"],
        claims=claims,
        analysis_pack=pack,
        qa_result=qa_result,
        updated_at="2026-07-18T00:00:00+00:00",
    )
    return pack, qa_result


def test_report_writer_blocks_rework_without_calling_model(monkeypatch, tmp_path: Path) -> None:
    _persist_pack_and_qa(monkeypatch, tmp_path, verdict="rework")
    calls = []

    result = run_report_writer(
        "mock-001",
        executor=lambda expert_id, payload: calls.append((expert_id, payload)) or {},
    )

    assert result["status"] == "blocked"
    assert result["reason"] == "qa_gate_rework"
    assert result["qa_verdict"] == "rework"
    assert calls == []
    assert get_report_artifact("mock-001") is None


def test_report_writer_persists_traceable_report_artifact_after_qa_pass(monkeypatch, tmp_path: Path) -> None:
    pack, qa_result = _persist_pack_and_qa(monkeypatch, tmp_path, verdict="pass")
    calls = []

    def fake_executor(expert_id: str, payload: dict) -> dict:
        calls.append((expert_id, payload))
        claim_id = pack["claims"][0]["id"]
        evidence_id = pack["evidence_items"][0]["id"]
        return _completed_writer(
            {
                "sections": [{"id": "summary", "title": "执行摘要", "content": "可追溯结论。"}],
                "claim_evidence_refs": [
                    {"section_id": "summary", "claim_ids": [claim_id], "evidence_ids": [evidence_id]}
                ],
                "risk_disclosures": [],
                "table_specs": [],
                "chart_specs": [],
                "trace_summary": {"source": "analysis_pack"},
            }
        )

    result = run_report_writer("mock-001", executor=fake_executor)
    artifact = get_report_artifact("mock-001")

    assert result["status"] == "completed"
    assert result["is_real_report_generation"] is True
    assert result["qa_verdict"] == qa_result["verdict"] == "pass"
    assert calls and calls[0][0] == "report_writer"
    assert calls[0][1]["analysis_pack"]["claims"] == pack["claims"]
    assert artifact["status"] == "delivered"
    assert artifact["payload"]["claim_evidence_refs"][0]["evidence_ids"] == [pack["evidence_items"][0]["id"]]
    assert get_report("mock-001")["data_source"] == "llm-report-writer-over-local-evidence"


def test_report_writer_rejects_untraceable_claim_reference(monkeypatch, tmp_path: Path) -> None:
    _persist_pack_and_qa(monkeypatch, tmp_path, verdict="pass")

    result = run_report_writer(
        "mock-001",
        executor=lambda *_: _completed_writer(
            {
                "sections": [{"id": "summary", "title": "执行摘要", "content": "不可追溯结论。"}],
                "claim_evidence_refs": [
                    {"section_id": "summary", "claim_ids": ["claim_not_in_pack"], "evidence_ids": []}
                ],
            }
        ),
    )

    assert result["status"] == "failed"
    assert result["reason"] == "report_output_untraceable"
    assert "unknown_claim_reference:0" in result["output_errors"]
    assert get_report_artifact("mock-001") is None
