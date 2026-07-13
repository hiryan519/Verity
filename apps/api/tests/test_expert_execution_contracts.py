from fastapi.testclient import TestClient

from verity_api.expert_execution_contracts import validate_execution_contract_coverage
from verity_api.main import app


client = TestClient(app)


def test_execution_contracts_cover_every_registered_expert() -> None:
    assert validate_execution_contract_coverage() is True

    response = client.get("/api/expert-execution-contracts")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data_source"]["mode"] == "expert-execution-contracts"
    assert payload["data_source"]["is_real_workflow"] is False
    assert len(payload["items"]) == 8
    assert all(item["is_real_llm_execution"] is False for item in payload["items"])
    assert all(item["is_page_editable"] is False for item in payload["items"])


def test_product_analyst_execution_contract_aligns_with_pack_type() -> None:
    response = client.get("/api/expert-execution-contracts/product_analyst")

    assert response.status_code == 200
    item = response.json()["item"]
    assert item["prompt_visibility"] == "internal_contract"
    assert any(field["name"] == "evidence_slice" for field in item["input_schema"])
    assert any(field["name"] == "claims" for field in item["output_schema"])
    assert "不要直接采集网页" in item["prompt_fragment"]


def test_ux_contract_requires_insufficient_evidence_behavior() -> None:
    response = client.get("/api/expert-execution-contracts/user_experience_analyst")

    assert response.status_code == 200
    item = response.json()["item"]
    output_names = {field["name"] for field in item["output_schema"]}
    assert "evidence_coverage" in output_names
    assert "semantic_risks" in output_names
    assert "insufficient_evidence" in item["prompt_fragment"]


def test_qa_contract_uses_qa_brief_not_full_pack() -> None:
    response = client.get("/api/expert-execution-contracts/qa_agent")

    assert response.status_code == 200
    item = response.json()["item"]
    input_names = {field["name"] for field in item["input_schema"]}
    assert "qa_brief" in input_names
    assert "analysis_packs" not in input_names
    assert "最多触发 1 次返工" in item["prompt_fragment"]


def test_report_writer_contract_forbids_new_claims_and_unsupported_charts() -> None:
    response = client.get("/api/expert-execution-contracts/report_writer")

    assert response.status_code == 200
    item = response.json()["item"]
    assert "不要新增 Analysis Pack 外的核心结论" in item["prompt_fragment"]
    assert "图表和表格必须来自通过 QA 的结构化数据" in item["prompt_fragment"]
    assert any(field["name"] == "chart_specs" for field in item["output_schema"])
