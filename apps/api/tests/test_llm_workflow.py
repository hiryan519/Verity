from pathlib import Path

from verity_api import db
from verity_api.db import get_qa_result, get_report, list_claims
from verity_api.llm_workflow import run_llm_expert_workflow


def _completed(expert_id: str, output: dict) -> dict:
    return {
        "status": "completed",
        "reason": "completed",
        "expert_id": expert_id,
        "provider_status": {"provider": "test", "model": "test-model", "model_tier": "fast"},
        "is_real_llm_execution": True,
        "mock_fallback_used": False,
        "output": output,
        "error": None,
        "trace_step": {"id": f"trace-{expert_id}"},
    }


def test_llm_workflow_persists_three_expert_chain_over_local_evidence(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "verity.db")
    calls = []

    def fake_executor(expert_id: str, payload: dict) -> dict:
        calls.append((expert_id, payload))
        if expert_id == "product_analyst":
            return _completed(
                expert_id,
                {
                    "claims": [{"claim_text": "Gamma supports presentation-oriented content generation.", "evidence_ids": ["ev_mock_002"]}],
                    "data_gaps": [],
                    "risk_notes": [],
                    "comparison_items": [],
                },
            )
        if expert_id == "pricing_analyst":
            return _completed(
                expert_id,
                {
                    "claims": [{"claim_text": "Notion AI pricing evidence is available from an official page.", "evidence_ids": ["ev_mock_001"]}],
                    "data_gaps": [],
                    "risk_notes": [],
                    "pricing_matrix": [],
                    "normalization_notes": [],
                },
            )
        if expert_id == "cross_validator":
            return _completed(
                expert_id,
                {
                    "claim_checks": [],
                    "conflicts": [],
                    "evidence_misuse": [],
                    "downgrade_suggestions": [],
                    "merged_data_gaps": [],
                },
            )
        return _completed(
            expert_id,
            {
                "qa_status": "pass",
                "scores": {},
                "hard_failures": [],
                "issues": [],
                "issue_handling_paths": [],
                "rework_count": 0,
            },
        )

    result = run_llm_expert_workflow("mock-001", executor=fake_executor)

    assert result["status"] == "completed"
    assert result["is_real_llm_execution"] is True
    assert result["is_real_research"] is False
    assert len(calls) == 4  # both parallel calls and their downstream calls happened
    assert {expert_id for expert_id, _ in calls} == {
        "product_analyst",
        "pricing_analyst",
        "cross_validator",
        "qa_agent",
    }
    assert len(result["analysis_pack"]["claims"]) == 2
    assert result["qa_gate"]["verdict"] == "pass"
    assert get_report("mock-001")["data_source"] == "llm-expert-over-local-evidence"
    assert len(list_claims("mock-001")) == 2
    assert get_qa_result("mock-001")["verdict"] == "pass"


def test_llm_workflow_blocks_unknown_report(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "verity.db")

    result = run_llm_expert_workflow("not-found", executor=lambda *_: {})

    assert result["status"] == "blocked"
    assert result["reason"] == "report_not_found"
    assert result["is_real_llm_execution"] is False
