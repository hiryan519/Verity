from fastapi.testclient import TestClient

from verity_api.main import app


client = TestClient(app)


def test_expert_registry_lists_confirmed_expert_types() -> None:
    response = client.get("/api/experts")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data_source"]["mode"] == "expert-registry"
    assert payload["data_source"]["is_real_workflow"] is False

    items = payload["items"]
    expert_ids = {item["id"] for item in items}
    assert expert_ids == {
        "research_orchestrator",
        "evidence_collector",
        "product_analyst",
        "pricing_analyst",
        "user_experience_analyst",
        "cross_validator",
        "qa_agent",
        "report_writer",
    }
    assert {item["layer"] for item in items} == {"L3 决策层", "L2 策略层", "L1 执行层"}


def test_expert_detail_exposes_governance_contract_not_runtime_wrapper() -> None:
    response = client.get("/api/experts/product_analyst")

    assert response.status_code == 200
    item = response.json()["item"]
    assert item["name"] == "产品分析专家"
    assert item["output_contract"]["pack_type"] == "Product Analysis Pack"
    assert item["supports_multi_instance"] is True
    assert "Evidence Slice" in item["instance_strategy"]
    assert any("不直接采集网页证据" in boundary for boundary in item["boundaries"])


def test_tool_permissions_hide_internal_capabilities() -> None:
    response = client.get("/api/experts/research_orchestrator")

    assert response.status_code == 200
    item = response.json()["item"]
    tool_keys = {tool["key"] for tool in item["tool_permissions"]}
    assert "trace_write" not in tool_keys
    assert "workflow_dispatch" not in tool_keys
    assert {tool["status"] for tool in item["tool_permissions"]} == {"disabled"}


def test_report_writer_uses_controlled_rendering_tools_not_general_code() -> None:
    response = client.get("/api/experts/report_writer")

    assert response.status_code == 200
    item = response.json()["item"]
    tools = {tool["key"]: tool["status"] for tool in item["tool_permissions"]}
    assert tools["report_renderer"] == "allowed"
    assert tools["table_generator"] == "allowed"
    assert tools["chart_spec_generator"] == "allowed"
    assert tools["citation_indexer"] == "allowed"
    assert tools["code_executor"] == "disabled"
    assert item["output_contract"]["pack_type"] == "Traceable Report Draft"


def test_unknown_expert_detail_returns_empty_item() -> None:
    response = client.get("/api/experts/not-a-real-expert")

    assert response.status_code == 200
    assert response.json()["item"] is None
