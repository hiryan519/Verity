from __future__ import annotations

from typing import Any


SUPPORTED_STATUSES = {"supported", "weakly_supported"}


def build_analysis_pack(
    report_id: str,
    research_goal: str,
    dimensions: list[str],
    claims: list[dict[str, Any]],
    evidence_items: list[dict[str, Any]],
) -> dict[str, Any]:
    evidence_by_id = {item["id"]: item for item in evidence_items}
    claim_evidence_map = []
    data_gaps = []
    conflicts = []

    for claim in claims:
        bound_evidence = [evidence_by_id[evidence_id] for evidence_id in claim.get("evidence_ids", []) if evidence_id in evidence_by_id]
        claim_evidence_map.append(
            {
                "claim_id": claim["id"],
                "evidence_ids": [item["id"] for item in bound_evidence],
                "max_confidence": max([item["confidence"] for item in bound_evidence], default=0),
                "evidence_levels": [item["confidence_level"] for item in bound_evidence],
            }
        )

        if not bound_evidence:
            data_gaps.append(f"Claim {claim['id']} 缺少证据绑定。")
        if claim["status"] == "conflicted":
            conflicts.append(f"Claim {claim['id']} 存在证据冲突。")
        if claim["status"] == "unsupported":
            data_gaps.append(f"Claim {claim['id']} 暂无可用证据支撑。")

    covered_dimensions = {claim["dimension"] for claim in claims if claim["status"] in SUPPORTED_STATUSES}
    for dimension in dimensions:
        if dimension not in covered_dimensions:
            data_gaps.append(f"分析维度「{dimension}」缺少可用结论。")

    confidence_summary = {
        "high": sum(1 for item in evidence_items if item["confidence_level"] == "high"),
        "medium": sum(1 for item in evidence_items if item["confidence_level"] == "medium"),
        "low": sum(1 for item in evidence_items if item["confidence_level"] == "low"),
    }

    return {
        "report_id": report_id,
        "research_goal": research_goal,
        "dimensions": dimensions,
        "claims": claims,
        "evidence_items": evidence_items,
        "claim_evidence_map": claim_evidence_map,
        "data_gaps": data_gaps,
        "conflicts": conflicts,
        "confidence_summary": confidence_summary,
        "ready_for_qa": True,
    }
