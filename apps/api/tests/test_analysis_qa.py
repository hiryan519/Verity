from verity_api.analysis import build_analysis_pack
from verity_api.qa import run_qa_gate


def test_supported_pack_passes_qa_gate() -> None:
    claims = [
        {
            "id": "claim_1",
            "text": "官方定价页可以支撑套餐边界判断。",
            "status": "supported",
            "strength": "strong",
            "dimension": "定价策略",
            "evidence_ids": ["ev_1"],
        }
    ]
    evidence = [
        {
            "id": "ev_1",
            "confidence": 86,
            "confidence_level": "high",
        }
    ]
    pack = build_analysis_pack("report_1", "研究定价策略", ["定价策略"], claims, evidence)
    result = run_qa_gate(pack)

    assert result["verdict"] == "pass"
    assert result["total_score"] >= 75
    assert not result["hard_failures"]


def test_missing_or_low_confidence_evidence_triggers_rework() -> None:
    claims = [
        {
            "id": "claim_1",
            "text": "用户普遍认为该产品协作体验领先。",
            "status": "supported",
            "strength": "strong",
            "dimension": "用户声音",
            "evidence_ids": ["ev_low"],
        },
        {
            "id": "claim_2",
            "text": "该产品企业版转化率显著更高。",
            "status": "unsupported",
            "strength": "strong",
            "dimension": "商业模式",
            "evidence_ids": [],
        },
    ]
    evidence = [
        {
            "id": "ev_low",
            "confidence": 42,
            "confidence_level": "low",
        }
    ]
    pack = build_analysis_pack("report_1", "研究用户声音", ["用户声音", "商业模式"], claims, evidence)
    result = run_qa_gate(pack)

    assert result["verdict"] == "rework"
    assert "strong_claim_supported_only_by_low_confidence_evidence" in result["hard_failures"]
    assert "claim_missing_evidence_binding" in result["hard_failures"]
    assert result["rework_count"] == 0
    assert result["max_rework_count"] == 1
