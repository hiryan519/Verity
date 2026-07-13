from __future__ import annotations

from datetime import date, datetime
from typing import Any


SOURCE_AUTHORITY = {
    "official": 19,
    "official_doc": 20,
    "primary": 18,
    "financial_report": 20,
    "research_report": 16,
    "mainstream_media": 15,
    "expert_blog": 12,
    "vertical_media": 11,
    "community": 8,
    "user_review": 8,
    "social": 6,
    "sample": 8,
    "aggregator": 3,
    "unknown": 2,
}

RELEVANCE = {
    "direct": 19,
    "partial": 14,
    "contextual": 8,
    "none": 2,
}

SPECIFICITY = {
    "high": 14,
    "medium": 10,
    "low": 6,
    "none": 2,
}

RISK_PENALTIES = {
    "fetch_failed": 8,
    "not_found": 8,
    "login_wall": 5,
    "paywall": 5,
    "summary_only": 4,
    "short_content": 4,
    "ad_page": 5,
    "seo_farm": 5,
    "stale": 4,
    "conflict": 6,
    "unclear_source": 5,
    "small_sample": 5,
}


def score_evidence(evidence: dict[str, Any], reference_date: date | None = None) -> dict[str, Any]:
    reference_date = reference_date or date.today()
    scores = {
        "source_authority": _score_source_authority(evidence),
        "relevance": _score_relevance(evidence),
        "verifiability": _score_verifiability(evidence),
        "freshness": _score_freshness(evidence, reference_date),
        "specificity": _score_specificity(evidence),
        "corroboration": _score_corroboration(evidence),
        "risk_penalty": _score_risk_penalty(evidence),
    }
    confidence = max(
        0,
        min(
            100,
            scores["source_authority"]
            + scores["relevance"]
            + scores["verifiability"]
            + scores["freshness"]
            + scores["specificity"]
            + scores["corroboration"]
            - scores["risk_penalty"],
        ),
    )

    return {
        "scores": scores,
        "confidence": confidence,
        "confidence_level": confidence_level(confidence),
        "risk_note": _risk_note(evidence, confidence),
    }


def confidence_level(confidence: int) -> str:
    if confidence >= 80:
        return "high"
    if confidence >= 50:
        return "medium"
    return "low"


def _score_source_authority(evidence: dict[str, Any]) -> int:
    source_type = evidence.get("source_type", "unknown")
    return SOURCE_AUTHORITY.get(source_type, SOURCE_AUTHORITY["unknown"])


def _score_relevance(evidence: dict[str, Any]) -> int:
    relevance = evidence.get("relevance", "none")
    return RELEVANCE.get(relevance, RELEVANCE["none"])


def _score_verifiability(evidence: dict[str, Any]) -> int:
    if evidence.get("retrieval_status") in {"failed", "not_found"}:
        return 1

    score = 0
    if evidence.get("url") or evidence.get("file_source"):
        score += 6
    if evidence.get("title"):
        score += 2
    if evidence.get("platform") or evidence.get("publisher"):
        score += 2
    if evidence.get("captured_at") or evidence.get("published_at"):
        score += 3
    if evidence.get("author"):
        score += 2

    return min(15, score)


def _score_freshness(evidence: dict[str, Any], reference_date: date) -> int:
    raw_date = evidence.get("published_at") or evidence.get("captured_at")
    if not raw_date:
        return 2

    try:
        parsed = datetime.fromisoformat(str(raw_date).replace("Z", "+00:00")).date()
    except ValueError:
        return 2

    months_old = (reference_date.year - parsed.year) * 12 + reference_date.month - parsed.month
    if months_old <= 6:
        return 10
    if months_old <= 18:
        return 7
    if months_old <= 36:
        return 4
    return 1


def _score_specificity(evidence: dict[str, Any]) -> int:
    specificity = evidence.get("specificity", "none")
    score = SPECIFICITY.get(specificity, SPECIFICITY["none"])

    signals = evidence.get("specific_signals", [])
    if len(signals) >= 2:
        score += 1

    return min(15, score)


def _score_corroboration(evidence: dict[str, Any]) -> int:
    if evidence.get("has_conflict"):
        return 1

    count = int(evidence.get("corroborating_sources", 0))
    if count >= 2:
        return 9
    if count == 1:
        return 6
    return 3


def _score_risk_penalty(evidence: dict[str, Any]) -> int:
    risk_flags = evidence.get("risk_flags", [])
    penalty = sum(RISK_PENALTIES.get(flag, 0) for flag in risk_flags)
    return min(10, penalty)


def _risk_note(evidence: dict[str, Any], confidence: int) -> str:
    risk_flags = evidence.get("risk_flags", [])
    if "small_sample" in risk_flags:
        return "样本不足，只能作为趋势或风险提示。"
    if "conflict" in risk_flags:
        return "存在证据冲突，结论必须降级或标注争议。"
    if confidence < 50:
        return "低可信证据，不应支撑强结论。"
    if confidence < 80:
        return "中可信证据，强结论需要交叉验证。"
    return "高可信证据，可支撑关键结论，但仍需保留来源与时效风险。"
