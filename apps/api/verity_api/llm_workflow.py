from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
from typing import Any, Callable
from uuid import uuid4

from .analysis import build_analysis_pack
from .db import get_report, list_evidence, persist_llm_workflow_result
from .expert_context import build_expert_context_from_db
from .llm_execution import execute_llm_expert
from .qa import run_qa_gate


DEFAULT_DIMENSIONS = ("产品定位", "定价策略")
PARALLEL_EXPERTS = ("product_analyst", "pricing_analyst")
ONLINE_PARALLEL_EXPERTS = ("product_analyst", "pricing_analyst", "user_experience_analyst")


def run_llm_expert_workflow(
    report_id: str,
    *,
    dimensions: list[str] | None = None,
    scope_overrides: dict[str, Any] | None = None,
    executor: Callable[[str, dict[str, Any]], dict[str, Any]] = execute_llm_expert,
    expert_ids: tuple[str, ...] | None = None,
    evidence_source: str = "local-db",
    is_real_research: bool = False,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Run the smallest governed LLM workflow over an existing evidence set.

    This adapter deliberately uses local evidence already stored for the report. It
    validates real expert execution and pack/QA wiring, but does not claim online
    research until the Tavily evidence adapter is connected.
    """

    report = get_report(report_id)
    if report is None:
        return {
            "status": "blocked",
            "reason": "report_not_found",
            "report_id": report_id,
            "is_real_llm_execution": False,
            "is_real_research": False,
        }

    run_id = run_id or f"llm_run_{uuid4().hex[:10]}"
    selected_experts = expert_ids or PARALLEL_EXPERTS
    selected_dimensions = dimensions or list(DEFAULT_DIMENSIONS)
    scope = _build_scope(report, selected_dimensions, scope_overrides or {})
    evidence_items = list_evidence(report_id)
    evidence_slice = [_evidence_slice_item(item) for item in evidence_items]
    base_payload = {
        "run_id": run_id,
        "report_id": report_id,
        "research_goal": report["summary"],
        "scope": scope,
    }

    expert_results: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=len(selected_experts)) as pool:
        futures = {
            pool.submit(
                executor,
                expert_id,
                _analysis_payload(
                    base_payload,
                    expert_id,
                    evidence_slice,
                ),
            ): expert_id
            for expert_id in selected_experts
        }
        for future in as_completed(futures):
            expert_id = futures[future]
            expert_results[expert_id] = future.result()

    if not _all_completed(expert_results, selected_experts):
        return _workflow_failure(run_id, report_id, expert_results, "parallel_expert_failed")

    claims = _normalize_claims(expert_results, evidence_items, run_id, selected_experts)
    analysis_pack = build_analysis_pack(
        report_id=report_id,
        research_goal=report["summary"],
        dimensions=selected_dimensions,
        claims=claims,
        evidence_items=evidence_items,
    )

    analysis_pack["workflow"] = {
        "run_id": run_id,
        "expert_ids": list(selected_experts),
        "evidence_source": evidence_source,
        "is_real_llm_execution": True,
        "is_real_research": is_real_research,
    }
    analysis_pack["expert_outputs"] = {
        expert_id: expert_results[expert_id].get("output", {}) for expert_id in selected_experts
    }
    expert_data_gaps = []
    for expert_id in selected_experts:
        output = expert_results[expert_id].get("output", {})
        for gap in output.get("data_gaps", []):
            if isinstance(gap, dict):
                expert_data_gaps.append(gap)
            elif str(gap).strip():
                expert_data_gaps.append({"dimension": expert_id, "gap": str(gap)})
    analysis_pack["expert_data_gaps"] = expert_data_gaps
    existing_gaps = analysis_pack.get("data_gaps", [])
    analysis_pack["data_gaps"] = [*existing_gaps, *expert_data_gaps]

    cross_payload = {
        **base_payload,
        "active_memory": _memory_context("cross_validator")[0],
        "candidate_memory_hints": _memory_context("cross_validator")[1],
        "analysis_packs": [
            {"expert_id": expert_id, "output": expert_results[expert_id].get("output", {})}
            for expert_id in selected_experts
        ],
        "claim_evidence_index": analysis_pack["claim_evidence_map"],
    }
    cross_result = executor("cross_validator", cross_payload)
    cross_retry_count = 0
    if is_real_research and not _completed(cross_result):
        cross_retry_count = 1
        cross_result = executor(
            "cross_validator",
            _compact_cross_retry_payload(cross_payload),
        )
    expert_results["cross_validator"] = cross_result
    if not _completed(cross_result):
        return _workflow_failure(run_id, report_id, expert_results, "cross_validation_failed", analysis_pack)

    cross_output = cross_result.get("output", {})
    qa_brief = _build_qa_brief(analysis_pack, cross_output)
    analysis_pack["cross_validation_pack"] = cross_output
    analysis_pack["qa_brief"] = qa_brief
    analysis_pack["workflow"]["cross_validation_retry_count"] = cross_retry_count

    qa_payload = {
        **base_payload,
        "active_memory": _memory_context("qa_agent")[0],
        "candidate_memory_hints": _memory_context("qa_agent")[1],
        "qa_brief": qa_brief,
        "cross_validation_pack": cross_output,
        "rework_count": 0,
    }
    qa_expert_result = executor("qa_agent", qa_payload)
    expert_results["qa_agent"] = qa_expert_result
    if not _completed(qa_expert_result):
        return _workflow_failure(run_id, report_id, expert_results, "qa_expert_failed", analysis_pack)

    analysis_pack["llm_qa_review"] = qa_expert_result.get("output", {})
    qa_gate_result = run_qa_gate(analysis_pack)
    persist_llm_workflow_result(
        report_id=report_id,
        title=report["title"],
        research_goal=report["summary"],
        competitors=report["competitors"],
        claims=claims,
        analysis_pack=analysis_pack,
        qa_result=qa_gate_result,
        updated_at=datetime.now(timezone.utc).isoformat(),
        data_source=("llm-expert-over-tavily-evidence" if is_real_research else "llm-expert-over-local-evidence"),
    )

    return {
        "status": "completed",
        "reason": "completed",
        "run_id": run_id,
        "report_id": report_id,
        "expert_results": {expert_id: _public_result(result) for expert_id, result in expert_results.items()},
        "analysis_pack": analysis_pack,
        "qa_gate": qa_gate_result,
        "is_real_workflow": True,
        "is_real_llm_execution": True,
        "is_real_research": is_real_research,
        "boundary": (
            "真实 LLM 专家执行 over Tavily-extracted public-web evidence."
            if is_real_research
            else "真实 LLM 专家执行 over local-db evidence; this is not online research."
        ),
    }


def _analysis_payload(
    base_payload: dict[str, Any],
    expert_id: str,
    evidence_slice: list[dict[str, Any]],
) -> dict[str, Any]:
    active_memory, candidate_memory = _memory_context(expert_id)
    return {
        **base_payload,
        "active_memory": active_memory,
        "candidate_memory_hints": candidate_memory,
        "evidence_slice": evidence_slice,
        "slice_budget": {
            "batch_id": "local-evidence-all",
            "max_tokens": 6000,
            "coverage": "all evidence currently stored for this report",
        },
    }


def _build_scope(report: dict[str, Any], dimensions: list[str], overrides: dict[str, Any]) -> dict[str, Any]:
    scope = {
        "competitors": report["competitors"],
        "dimensions": dimensions,
        "market": "not_specified",
        "audience": "not_specified",
        "time_range": "current_report_scope",
    }
    if isinstance(report.get("scope"), dict):
        scope.update(report["scope"])
    scope["dimensions"] = dimensions
    scope.update(overrides)
    return scope


def _memory_context(expert_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    context = build_expert_context_from_db(expert_id)
    return context["checklist_context"], context["trial_hints"]


def _evidence_slice_item(item: dict[str, Any]) -> dict[str, Any]:
    content_hash = hashlib.sha256(
        "\n".join(str(item.get(key, "")) for key in ("title", "url", "summary")).encode("utf-8")
    ).hexdigest()
    return {
        "id": item["id"],
        "title": item["title"],
        "url": item.get("url"),
        "excerpt": item.get("summary", ""),
        "score": item.get("confidence", 0),
        "confidence_level": item.get("confidence_level", "low"),
        "risk": item.get("risk_note", ""),
        "content_hash": content_hash,
    }


def _normalize_claims(
    expert_results: dict[str, dict[str, Any]],
    evidence_items: list[dict[str, Any]],
    run_id: str,
    expert_ids: tuple[str, ...],
) -> list[dict[str, Any]]:
    evidence_by_id = {item["id"]: item for item in evidence_items}
    claims: list[dict[str, Any]] = []
    dimensions = {
        "product_analyst": "产品定位",
        "pricing_analyst": "定价策略",
        "user_experience_analyst": "用户体验",
    }
    for expert_id in expert_ids:
        output = expert_results[expert_id].get("output", {})
        raw_claims = output.get("claims", [])
        if expert_id == "user_experience_analyst":
            raw_claims = output.get("experience_claims", [])
        for index, raw_claim in enumerate(raw_claims):
            if not isinstance(raw_claim, dict):
                continue
            text = raw_claim.get("claim_text") or raw_claim.get("claim") or raw_claim.get("text")
            if not isinstance(text, str) or not text.strip():
                continue
            evidence_ids = [
                evidence_id for evidence_id in raw_claim.get("evidence_ids", []) if evidence_id in evidence_by_id
            ]
            levels = [evidence_by_id[evidence_id].get("confidence_level", "low") for evidence_id in evidence_ids]
            requested_status = raw_claim.get("claim_status") or raw_claim.get("status")
            status = requested_status if requested_status in {"supported", "weakly_supported", "conflicted", "unresolved", "unsupported"} else _status_from_evidence(levels)
            risk_note = raw_claim.get("risk_note") or raw_claim.get("risks") or ""
            if isinstance(risk_note, list):
                risk_note = "; ".join(str(item) for item in risk_note)
            claims.append(
                {
                    "id": f"claim_{run_id}_{expert_id}_{index}",
                    "text": text.strip(),
                    "status": status,
                    "strength": "strong" if status == "supported" and "high" in levels else "weak",
                    "dimension": raw_claim.get("dimension") or dimensions.get(expert_id, "未分类"),
                    "evidence_ids": evidence_ids,
                    "risk_note": str(risk_note),
                }
            )
    return claims


def _status_from_evidence(levels: list[str]) -> str:
    if "high" in levels or levels.count("medium") >= 2:
        return "supported"
    if levels:
        return "weakly_supported"
    return "unsupported"


def _build_qa_brief(analysis_pack: dict[str, Any], cross_output: dict[str, Any]) -> dict[str, Any]:
    return {
        "claim_count": len(analysis_pack.get("claims", [])),
        "evidence_count": len(analysis_pack.get("evidence_items", [])),
        "data_gap_count": len(analysis_pack.get("data_gaps", [])),
        "conflict_count": len(cross_output.get("conflicts", [])),
        "evidence_misuse_count": len(cross_output.get("evidence_misuse", [])),
        "issues": [
            *analysis_pack.get("data_gaps", [])[:5],
            *cross_output.get("downgrade_suggestions", [])[:5],
        ],
    }


def _compact_cross_retry_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Retry cross validation with only comparison-relevant fields.

    A failed structured response should not be retried with the same oversized
    pack. The retry preserves claim/evidence mappings, gaps and risks while
    dropping long narrative fields and pricing tables.
    """
    compact_packs = []
    for pack in payload.get("analysis_packs", []):
        output = pack.get("output", {}) if isinstance(pack, dict) else {}
        claims = output.get("claims") or output.get("experience_claims") or []
        compact_output = {
            "claims": claims[:30] if isinstance(claims, list) else [],
            "data_gaps": output.get("data_gaps", [])[:12] if isinstance(output.get("data_gaps", []), list) else [],
            "risk_notes": output.get("risk_notes", [])[:12] if isinstance(output.get("risk_notes", []), list) else [],
            "semantic_risks": output.get("semantic_risks", [])[:12] if isinstance(output.get("semantic_risks", []), list) else [],
        }
        compact_packs.append({"expert_id": pack.get("expert_id"), "output": compact_output})
    return {
        **payload,
        "analysis_packs": compact_packs,
        "retry_instruction": "上一次交叉验证输出未通过结构化校验。本次仅返回符合输出结构约束的 JSON，不要添加 Markdown、解释文字或额外字段。",
    }


def _all_completed(results: dict[str, dict[str, Any]], expert_ids: tuple[str, ...]) -> bool:
    return all(_completed(results.get(expert_id, {})) for expert_id in expert_ids)


def _completed(result: dict[str, Any]) -> bool:
    return result.get("status") == "completed" and result.get("is_real_llm_execution") is True


def _workflow_failure(
    run_id: str,
    report_id: str,
    expert_results: dict[str, dict[str, Any]],
    reason: str,
    analysis_pack: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "status": "failed",
        "reason": reason,
        "run_id": run_id,
        "report_id": report_id,
        "expert_results": {expert_id: _public_result(result) for expert_id, result in expert_results.items()},
        "analysis_pack": analysis_pack,
        "is_real_workflow": False,
        "is_real_llm_execution": any(_completed(result) for result in expert_results.values()),
        "is_real_research": False,
    }


def _public_result(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": result.get("status"),
        "reason": result.get("reason"),
        "expert_id": result.get("expert_id"),
        "provider_status": result.get("provider_status"),
        "is_real_llm_execution": result.get("is_real_llm_execution", False),
        "mock_fallback_used": result.get("mock_fallback_used", False),
        "output": result.get("output", {}),
        "error": result.get("error"),
        "trace_step_id": (result.get("trace_step") or {}).get("id"),
    }
