from fastapi.testclient import TestClient

from verity_api.main import app


client = TestClient(app)


def test_feedback_creates_expert_lesson_candidate() -> None:
    response = client.post(
        "/api/memories/from-feedback",
        json={
            "report_id": "mock-001",
            "target_agent": "business_pricing_analyst",
            "feedback": "价格和 token 之间是什么关系？同样价格下哪个 API 可调用次数最多？",
            "source_ref": "annotation_mock_001",
        },
    )

    assert response.status_code == 200
    item = response.json()["item"]
    assert item["memory_type"] == "expert_lesson"
    assert item["status"] == "candidate"
    assert item["target_agent"] == "business_pricing_analyst"
    assert item["influence_target"] == "agent_checklist"
    assert "token" in item["content"]


def test_active_memory_changes_next_expert_run() -> None:
    created = client.post(
        "/api/memories/candidates",
        json={
            "memory_type": "expert_lesson",
            "content": "价格分析必须比较同预算下的 token 可用量和套餐限制。",
            "target_agent": "business_pricing_analyst",
            "influence_target": "agent_checklist",
            "source_type": "user_annotation",
            "source_report_id": "mock-001",
            "confidence": 82,
            "status": "candidate",
        },
    ).json()["item"]

    activated = client.post(f"/api/memories/{created['id']}/activate").json()["item"]
    assert activated["status"] == "active"

    run = client.post("/api/verity/experts/run-minimal?report_id=mock-001").json()["item"]
    pricing_result = next(result for result in run["expert_results"] if result["expert_id"] == "business_pricing_analyst")

    assert created["id"] in pricing_result["trace"]["applied_memory_ids"]
    assert "价格分析必须比较同预算下的 token 可用量和套餐限制。" in pricing_result["output"]["checklist_additions"]


def test_low_confidence_memory_cannot_be_activated() -> None:
    created = client.post(
        "/api/memories/candidates",
        json={
            "memory_type": "expert_lesson",
            "content": "低可信反馈不应直接影响专家。",
            "target_agent": "qa_agent",
            "influence_target": "agent_checklist",
            "source_type": "user_annotation",
            "confidence": 40,
            "status": "candidate",
        },
    ).json()["item"]

    activated = client.post(f"/api/memories/{created['id']}/activate").json()["item"]

    assert activated["status"] == "quarantined"


def test_knowledge_item_can_be_cited_as_evidence_and_memory_candidate() -> None:
    response = client.post(
        "/api/knowledge/cite-as-evidence",
        json={"report_id": "mock-001", "knowledge_id": "kn_mock_pricing_token_value"},
    )

    assert response.status_code == 200
    item = response.json()["item"]
    assert item["evidence"]["source_type"] == "user_knowledge"
    assert item["memory_candidate"]["status"] == "candidate"
    assert item["memory_candidate"]["source_type"] == "knowledge_highlight"


def test_candidate_memory_is_trial_suggestion_not_checklist_addition() -> None:
    created = client.post(
        "/api/memories/candidates",
        json={
            "memory_type": "expert_lesson",
            "content": "候选经验只应作为建议，不应直接进入 checklist。",
            "target_agent": "business_pricing_analyst",
            "influence_target": "agent_checklist",
            "source_type": "knowledge_highlight",
            "source_report_id": "mock-001",
            "confidence": 76,
            "status": "candidate",
        },
    ).json()["item"]

    run = client.post("/api/verity/experts/run-minimal?report_id=mock-001").json()["item"]
    pricing_result = next(result for result in run["expert_results"] if result["expert_id"] == "business_pricing_analyst")

    assert created["id"] in pricing_result["trace"]["candidate_memory_ids"]
    assert any(suggestion["id"] == created["id"] for suggestion in pricing_result["output"]["candidate_suggestions"])
    assert created["content"] not in pricing_result["output"]["checklist_additions"]


def test_negative_signal_quarantines_memory_candidate() -> None:
    created = client.post(
        "/api/memories/candidates",
        json={
            "memory_type": "expert_lesson",
            "content": "这条候选经验会被用户负反馈隔离。",
            "target_agent": "business_pricing_analyst",
            "influence_target": "agent_checklist",
            "source_type": "knowledge_highlight",
            "confidence": 76,
            "status": "candidate",
        },
    ).json()["item"]

    updated = client.post(f"/api/memories/{created['id']}/signal", json={"signal": "negative"}).json()["item"]

    assert updated["status"] == "quarantined"
    assert updated["negative_signal_count"] >= 1


def test_memory_candidate_accepts_effect_strategy_alias() -> None:
    created = client.post(
        "/api/memories/candidates",
        json={
            "memory_type": "expert_lesson",
            "content": "使用生效策略别名创建候选记忆。",
            "target_agent": "business_pricing_analyst",
            "effect_strategy": "agent_checklist",
            "source_type": "user_annotation",
            "confidence": 80,
            "status": "candidate",
        },
    ).json()["item"]

    assert created["effect_strategy"] == "agent_checklist"
    assert created["influence_target"] == "agent_checklist"
