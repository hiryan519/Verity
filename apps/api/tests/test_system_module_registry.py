from fastapi.testclient import TestClient

from verity_api.main import app


client = TestClient(app)


def test_system_module_registry_lists_non_expert_modules() -> None:
    response = client.get("/api/system-modules")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data_source"]["mode"] == "system-module-registry"
    assert payload["data_source"]["is_real_workflow"] is False

    items = payload["items"]
    module_ids = {item["id"] for item in items}
    assert module_ids == {"evidence_router", "qa_brief_builder", "report_renderer"}
    assert all(item["is_expert"] is False for item in items)


def test_system_modules_do_not_appear_in_expert_registry() -> None:
    response = client.get("/api/experts")

    assert response.status_code == 200
    expert_ids = {item["id"] for item in response.json()["items"]}
    assert "evidence_router" not in expert_ids
    assert "qa_brief_builder" not in expert_ids
    assert "report_renderer" not in expert_ids


def test_evidence_router_contract_preserves_traceable_slices() -> None:
    response = client.get("/api/system-modules/evidence_router")

    assert response.status_code == 200
    item = response.json()["item"]
    assert item["name"] == "Evidence Router / Evidence Slice"
    assert item["uses_llm"] is False
    assert "Evidence Slice" in item["io_contract"]["outputs"]
    assert any("不可追溯摘要" in boundary for boundary in item["boundaries"])
    assert any("content_hash" in requirement for requirement in item["trace_requirements"])


def test_qa_brief_builder_is_rule_based_not_llm_summarizer() -> None:
    response = client.get("/api/system-modules/qa_brief_builder")

    assert response.status_code == 200
    item = response.json()["item"]
    assert item["uses_llm"] is False
    assert any("不是 LLM 总结器" in boundary for boundary in item["boundaries"])
    assert "QA Brief" in item["io_contract"]["outputs"]


def test_report_renderer_cannot_create_unsupported_charts() -> None:
    response = client.get("/api/system-modules/report_renderer")

    assert response.status_code == 200
    item = response.json()["item"]
    assert item["uses_llm"] is False
    assert any("没有数据表支撑的图表" in boundary for boundary in item["boundaries"])
    assert "HTML report" in item["io_contract"]["outputs"]
