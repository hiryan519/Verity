from datetime import date

from verity_api.scoring import score_evidence


REFERENCE_DATE = date(2026, 7, 10)


def test_official_direct_evidence_scores_high() -> None:
    result = score_evidence(
        {
            "source_type": "official",
            "relevance": "direct",
            "url": "https://example.com/pricing",
            "title": "Pricing",
            "platform": "example",
            "captured_at": "2026-07-10",
            "specificity": "high",
            "specific_signals": ["price", "plan"],
            "corroborating_sources": 2,
            "risk_flags": [],
        },
        reference_date=REFERENCE_DATE,
    )

    assert result["confidence_level"] == "high"
    assert result["confidence"] >= 80
    assert result["scores"]["source_authority"] >= 18


def test_small_sample_user_voice_is_not_high_confidence() -> None:
    result = score_evidence(
        {
            "source_type": "user_review",
            "relevance": "partial",
            "url": "#sample",
            "title": "User Voice Sample",
            "platform": "mock",
            "captured_at": "2026-07-10",
            "specificity": "medium",
            "corroborating_sources": 0,
            "risk_flags": ["small_sample"],
        },
        reference_date=REFERENCE_DATE,
    )

    assert result["confidence_level"] == "medium"
    assert result["confidence"] < 80
    assert "样本不足" in result["risk_note"]


def test_failed_fetch_scores_low() -> None:
    result = score_evidence(
        {
            "source_type": "unknown",
            "relevance": "none",
            "retrieval_status": "failed",
            "specificity": "none",
            "risk_flags": ["fetch_failed", "unclear_source"],
        },
        reference_date=REFERENCE_DATE,
    )

    assert result["confidence_level"] == "low"
    assert result["confidence"] < 50
    assert result["scores"]["verifiability"] <= 3
