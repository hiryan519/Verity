from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable
from uuid import uuid4

from .db import (
    get_analysis_pack,
    get_qa_result,
    get_report,
    persist_report_artifact,
)
from .expert_context import build_expert_context_from_db
from .llm_execution import execute_llm_expert


ALLOWED_QA_VERDICTS = {"pass", "pass_with_risk"}


def run_report_writer(
    report_id: str,
    *,
    report_outline: dict[str, Any] | None = None,
    executor: Callable[[str, dict[str, Any]], dict[str, Any]] = execute_llm_expert,
) -> dict[str, Any]:
    """Generate a traceable report artifact only after the QA Gate allows it."""
    report = get_report(report_id)
    if report is None:
        return _blocked(report_id, "report_not_found")

    analysis_pack = get_analysis_pack(report_id)
    qa_result = get_qa_result(report_id)
    if analysis_pack is None or qa_result is None:
        return _blocked(report_id, "analysis_pack_or_qa_missing")
    if qa_result.get("verdict") not in ALLOWED_QA_VERDICTS:
        return {
            **_blocked(report_id, "qa_gate_rework"),
            "qa_verdict": qa_result.get("verdict"),
            "qa_issues": qa_result.get("issues", []),
            "recommendations": qa_result.get("recommendations", []),
        }

    run_id = f"writer_run_{uuid4().hex[:10]}"
    outline = report_outline or _default_outline(analysis_pack)
    context = build_expert_context_from_db("report_writer")
    payload = {
        "run_id": run_id,
        "report_id": report_id,
        "research_goal": report["summary"],
        "scope": report.get("scope", {}),
        "active_memory": context["checklist_context"],
        "candidate_memory_hints": context["trial_hints"],
        "analysis_pack": _writer_pack(analysis_pack),
        "qa_gate_result": qa_result,
        "claim_evidence_index": analysis_pack.get("claim_evidence_map", []),
        "report_outline": outline,
    }
    result = executor("report_writer", payload)
    if not _completed(result):
        return {
            "status": "failed",
            "reason": "report_writer_failed",
            "run_id": run_id,
            "report_id": report_id,
            "qa_verdict": qa_result.get("verdict"),
            "expert_result": _public_result(result),
            "is_real_report_generation": False,
        }

    output = result.get("output", {})
    output_errors = _validate_report_output(output, analysis_pack)
    if output_errors:
        return {
            "status": "failed",
            "reason": "report_output_untraceable",
            "run_id": run_id,
            "report_id": report_id,
            "qa_verdict": qa_result.get("verdict"),
            "output_errors": output_errors,
            "expert_result": _public_result(result),
            "is_real_report_generation": False,
        }

    artifact_payload = {
        "run_id": run_id,
        "report_id": report_id,
        "research_goal": report["summary"],
        "qa_verdict": qa_result["verdict"],
        "sections": output.get("sections", []),
        "claim_evidence_refs": output.get("claim_evidence_refs", []),
        "risk_disclosures": output.get("risk_disclosures", []),
        "table_specs": output.get("table_specs", []),
        "chart_specs": output.get("chart_specs", []),
        "trace_summary": output.get("trace_summary", {}),
    }
    artifact = persist_report_artifact(
        report_id=report_id,
        qa_verdict=qa_result["verdict"],
        payload=artifact_payload,
        created_at=datetime.now(timezone.utc).isoformat(),
        data_source=(
            "llm-report-writer-over-tavily-evidence"
            if report.get("data_source") == "llm-expert-over-tavily-evidence"
            else "llm-report-writer-over-local-evidence"
        ),
    )
    return {
        "status": "completed",
        "reason": "completed",
        "run_id": run_id,
        "report_id": report_id,
        "qa_verdict": qa_result["verdict"],
        "artifact": artifact,
        "expert_result": _public_result(result),
        "is_real_report_generation": True,
        "is_real_research": report.get("data_source") == "llm-expert-over-tavily-evidence",
    }


def _writer_pack(analysis_pack: dict[str, Any]) -> dict[str, Any]:
    """Pass only report-writing material, not duplicated expert narratives."""
    fields = (
        "report_id",
        "research_goal",
        "dimensions",
        "claims",
        "evidence_items",
        "claim_evidence_map",
        "data_gaps",
        "conflicts",
        "confidence_summary",
        "cross_validation_pack",
        "qa_brief",
    )
    return {field: analysis_pack.get(field) for field in fields if field in analysis_pack}


def _default_outline(analysis_pack: dict[str, Any]) -> dict[str, Any]:
    return {
        "sections": [
            {"id": "summary", "title": "执行摘要"},
            *[
                {"id": f"dimension_{index + 1}", "title": dimension}
                for index, dimension in enumerate(analysis_pack.get("dimensions", []))
            ],
            {"id": "risk", "title": "数据缺口与风险"},
        ]
    }


def _validate_report_output(output: dict[str, Any], analysis_pack: dict[str, Any]) -> list[str]:
    errors = []
    if not isinstance(output, dict):
        return ["output_not_object"]
    if not isinstance(output.get("sections"), list) or not output["sections"]:
        errors.append("sections_missing")
    if not isinstance(output.get("claim_evidence_refs"), list):
        errors.append("claim_evidence_refs_missing")
        return errors

    allowed_claims = {claim.get("id") for claim in analysis_pack.get("claims", [])}
    allowed_evidence = {item.get("id") for item in analysis_pack.get("evidence_items", [])}
    for index, ref in enumerate(output["claim_evidence_refs"]):
        if not isinstance(ref, dict):
            errors.append(f"claim_evidence_ref_not_object:{index}")
            continue
        claim_ids = ref.get("claim_ids", [])
        if ref.get("claim_id"):
            claim_ids = [*claim_ids, ref["claim_id"]]
        evidence_ids = ref.get("evidence_ids", [])
        if ref.get("evidence_id"):
            evidence_ids = [*evidence_ids, ref["evidence_id"]]
        if any(claim_id not in allowed_claims for claim_id in claim_ids):
            errors.append(f"unknown_claim_reference:{index}")
        if any(evidence_id not in allowed_evidence for evidence_id in evidence_ids):
            errors.append(f"unknown_evidence_reference:{index}")
    return errors


def _completed(result: dict[str, Any]) -> bool:
    return result.get("status") == "completed" and result.get("is_real_llm_execution") is True


def _blocked(report_id: str, reason: str) -> dict[str, Any]:
    return {
        "status": "blocked",
        "reason": reason,
        "report_id": report_id,
        "is_real_report_generation": False,
    }


def _public_result(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": result.get("status"),
        "reason": result.get("reason"),
        "expert_id": result.get("expert_id"),
        "provider_status": result.get("provider_status"),
        "is_real_llm_execution": result.get("is_real_llm_execution", False),
        "output": result.get("output", {}),
        "error": result.get("error"),
        "trace_step_id": (result.get("trace_step") or {}).get("id"),
    }
