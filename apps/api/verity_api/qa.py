from __future__ import annotations

from typing import Any


QA_WEIGHTS = {
    "evidence_sufficiency": 25,
    "dimension_coverage": 15,
    "claim_reliability": 20,
    "structured_completeness": 15,
    "evidence_consistency": 15,
    "data_gap_risk": 10,
}

REQUIRED_PACK_FIELDS = {
    "report_id",
    "research_goal",
    "dimensions",
    "claims",
    "evidence_items",
    "claim_evidence_map",
    "data_gaps",
    "conflicts",
    "confidence_summary",
    "ready_for_qa",
}


def run_qa_gate(analysis_pack: dict[str, Any], rework_count: int = 0) -> dict[str, Any]:
    hard_failures = _hard_failures(analysis_pack)
    scores = {
        "evidence_sufficiency": _score_evidence_sufficiency(analysis_pack),
        "dimension_coverage": _score_dimension_coverage(analysis_pack),
        "claim_reliability": _score_claim_reliability(analysis_pack),
        "structured_completeness": _score_structured_completeness(analysis_pack),
        "evidence_consistency": _score_evidence_consistency(analysis_pack),
        "data_gap_risk": _score_data_gap_risk(analysis_pack),
    }
    total_score = round(sum(scores[key] * QA_WEIGHTS[key] for key in scores) / 100)
    verdict = "pass" if total_score >= 75 and not hard_failures else "rework"

    return {
        "verdict": verdict,
        "total_score": total_score,
        "scores": scores,
        "hard_failures": hard_failures,
        "issues": _issues(analysis_pack, hard_failures),
        "recommendations": _recommendations(hard_failures),
        "rework_count": rework_count,
        "max_rework_count": 1,
    }


def _hard_failures(analysis_pack: dict[str, Any]) -> list[str]:
    failures = []
    if REQUIRED_PACK_FIELDS - set(analysis_pack):
        failures.append("analysis_pack_missing_required_fields")

    for claim in analysis_pack.get("claims", []):
        evidence_map = _evidence_map_for_claim(analysis_pack, claim["id"])
        evidence_levels = evidence_map.get("evidence_levels", [])
        if not evidence_map.get("evidence_ids"):
            failures.append("claim_missing_evidence_binding")
        if claim.get("strength") == "strong" and evidence_levels and set(evidence_levels) == {"low"}:
            failures.append("strong_claim_supported_only_by_low_confidence_evidence")
        if claim.get("status") in {"unsupported", "conflicted"} and claim.get("strength") == "strong":
            failures.append("unsupported_or_conflicted_claim_marked_as_strong")

    if analysis_pack.get("data_gaps") and not isinstance(analysis_pack.get("data_gaps"), list):
        failures.append("data_gaps_not_structured")
    if _score_dimension_coverage(analysis_pack) < 100:
        failures.append("core_dimension_missing")

    return sorted(set(failures))


def _score_evidence_sufficiency(analysis_pack: dict[str, Any]) -> int:
    maps = analysis_pack.get("claim_evidence_map", [])
    if not maps:
        return 0
    bound_count = sum(1 for item in maps if item.get("evidence_ids"))
    return round(bound_count / len(maps) * 100)


def _score_dimension_coverage(analysis_pack: dict[str, Any]) -> int:
    dimensions = set(analysis_pack.get("dimensions", []))
    if not dimensions:
        return 0
    covered = {claim.get("dimension") for claim in analysis_pack.get("claims", []) if claim.get("status") in {"supported", "weakly_supported"}}
    return round(len(dimensions & covered) / len(dimensions) * 100)


def _score_claim_reliability(analysis_pack: dict[str, Any]) -> int:
    claims = analysis_pack.get("claims", [])
    if not claims:
        return 0

    reliable = 0
    for claim in claims:
        evidence_map = _evidence_map_for_claim(analysis_pack, claim["id"])
        levels = evidence_map.get("evidence_levels", [])
        if claim.get("status") == "supported" and ("high" in levels or levels.count("medium") >= 2):
            reliable += 1
        elif claim.get("status") == "weakly_supported" and levels:
            reliable += 0.6
    return round(reliable / len(claims) * 100)


def _score_structured_completeness(analysis_pack: dict[str, Any]) -> int:
    present = len(set(analysis_pack) & REQUIRED_PACK_FIELDS)
    return round(present / len(REQUIRED_PACK_FIELDS) * 100)


def _score_evidence_consistency(analysis_pack: dict[str, Any]) -> int:
    conflicts = analysis_pack.get("conflicts", [])
    if not conflicts:
        return 100
    return max(20, 100 - len(conflicts) * 25)


def _score_data_gap_risk(analysis_pack: dict[str, Any]) -> int:
    gaps = analysis_pack.get("data_gaps", [])
    if not gaps:
        return 100
    return max(20, 100 - len(gaps) * 15)


def _evidence_map_for_claim(analysis_pack: dict[str, Any], claim_id: str) -> dict[str, Any]:
    for item in analysis_pack.get("claim_evidence_map", []):
        if item.get("claim_id") == claim_id:
            return item
    return {}


def _issues(analysis_pack: dict[str, Any], hard_failures: list[str]) -> list[str]:
    issues = []
    if hard_failures:
        issues.append("Analysis Pack 触发硬门槛失败，不能直接进入无风险报告生成。")
    issues.extend(analysis_pack.get("data_gaps", [])[:3])
    issues.extend(analysis_pack.get("conflicts", [])[:3])
    return issues


def _recommendations(hard_failures: list[str]) -> list[str]:
    recommendations = []
    if "claim_missing_evidence_binding" in hard_failures:
        recommendations.append("为关键 claim 绑定可复查证据，或将其降级为数据缺口。")
    if "strong_claim_supported_only_by_low_confidence_evidence" in hard_failures:
        recommendations.append("强结论需要高可信证据或多条中可信证据交叉支持。")
    if "unsupported_or_conflicted_claim_marked_as_strong" in hard_failures:
        recommendations.append("将 unsupported / conflicted claim 降级，或显式标注争议。")
    if "core_dimension_missing" in hard_failures:
        recommendations.append("补充缺失维度的证据与结论，或在报告中显式标注该维度为数据缺口。")
    if not recommendations:
        recommendations.append("保持风险提示，并在报告中展示数据缺口。")
    return recommendations
