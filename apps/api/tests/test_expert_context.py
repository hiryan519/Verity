from fastapi.testclient import TestClient

from verity_api.expert_context import build_expert_context
from verity_api.main import app


client = TestClient(app)


def test_active_memory_enters_checklist_context_not_evidence() -> None:
    context = build_expert_context(
        expert_id="pricing_analyst",
        active_memories=[
            {
                "id": "mem_active",
                "target_agent": "pricing_analyst",
                "content": "比较 API 价格时必须换算到同预算 token 可用量。",
                "effect_strategy": "agent_checklist",
                "source_type": "qa_rework",
            }
        ],
        candidate_memories=[],
        mounted_skills=[],
    )

    assert context["checklist_context"][0]["memory_id"] == "mem_active"
    assert context["checklist_context"][0]["not_fact_evidence"] is True
    assert context["context_policy"]["not_evidence"] is True


def test_candidate_memory_is_trial_hint_only() -> None:
    context = build_expert_context(
        expert_id="product_analyst",
        active_memories=[],
        candidate_memories=[
            {
                "id": "mem_candidate",
                "target_agent": "product_analyst",
                "content": "优先区分官网宣传和可复查产品能力。",
                "effect_strategy": "agent_checklist",
                "source_type": "user_annotation",
            }
        ],
        mounted_skills=[],
    )

    hint = context["trial_hints"][0]
    assert hint["memory_id"] == "mem_candidate"
    assert hint["trial_policy"] == "low_weight_target_expert_only"
    assert hint["not_fact_evidence"] is True
    assert "must not support factual claims" in hint["risk_note"]


def test_skill_context_requires_versioned_mounted_target_skill() -> None:
    context = build_expert_context(
        expert_id="report_writer",
        active_memories=[],
        candidate_memories=[],
        mounted_skills=[
            {
                "skill_id": "risk_disclosure_style",
                "name": "风险提示表达",
                "version": "v0.1",
                "summary": "将 QA 风险写入摘要和相关章节。",
                "target_expert": "report_writer",
            },
            {
                "skill_id": "unversioned",
                "name": "未治理方法",
                "version": "draft",
                "summary": "不应进入上下文。",
                "target_expert": "report_writer",
            },
            {
                "skill_id": "wrong_target",
                "name": "其他专家方法",
                "version": "v0.1",
                "summary": "不应进入当前专家上下文。",
                "target_expert": "pricing_analyst",
            },
        ],
    )

    assert [skill["skill_id"] for skill in context["mounted_skills"]] == ["risk_disclosure_style"]
    assert context["context_policy"]["skill_use"] == "versioned_mounted_methods_only"


def test_runtime_context_endpoint_uses_db_memories() -> None:
    created = client.post(
        "/api/memories/candidates",
        json={
            "memory_type": "expert_lesson",
            "content": "定价分析需要披露企业版价格不透明。",
            "target_agent": "pricing_analyst",
            "effect_strategy": "agent_checklist",
            "source_type": "user_annotation",
            "confidence": 82,
            "status": "candidate",
        },
    ).json()["item"]
    client.post(f"/api/memories/{created['id']}/activate")

    response = client.get("/api/experts/pricing_analyst/runtime-context")

    assert response.status_code == 200
    item = response.json()["item"]
    assert any(memory["memory_id"] == created["id"] for memory in item["checklist_context"])
    assert item["context_policy"]["not_evidence"] is True
