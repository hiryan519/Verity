MOCK_DATA_SOURCE = {
    "mode": "mock",
    "is_real_workflow": False,
    "note": "Phase 1 only exposes mock product-shape data. It is not real online collection.",
}

MOCK_NAVIGATION = [
    {"label": "工作台", "href": "/workspace"},
    {"label": "我的调研", "href": "/research"},
    {"label": "知识库", "href": "/knowledge"},
    {"label": "专家公会", "href": "/experts"},
    {"label": "竞争情报中心", "href": "/intelligence"},
]

MOCK_REPORTS = [
    {
        "id": "mock-001",
        "title": "AI 协作写作竞品分析",
        "competitors": ["Notion AI", "飞书妙记", "Gamma"],
        "evidence_count": 9,
        "claim_count": 6,
        "high_confidence_count": 3,
        "qa_status": "pass",
        "updated_at": "2026-07-10",
        "data_source": "mock",
    },
    {
        "id": "mock-002",
        "title": "B2B SaaS 定价策略研究",
        "competitors": ["Linear", "Jira", "Asana"],
        "evidence_count": 6,
        "claim_count": 4,
        "high_confidence_count": 2,
        "qa_status": "risk",
        "updated_at": "2026-07-09",
        "data_source": "mock",
    },
]

MOCK_EXPERTS = [
    {
        "id": "orchestrator",
        "name": "Research Orchestrator",
        "layer": "decision",
        "tool_scope": ["workflow", "trace", "expert_router"],
        "output_schema": "research_plan",
    },
    {
        "id": "evidence-collector",
        "name": "Evidence Collector",
        "layer": "execution",
        "tool_scope": ["web_fetch", "file_to_text"],
        "output_schema": "evidence_items",
    },
]
