from fastapi.testclient import TestClient

from verity_api.main import app


client = TestClient(app)


def test_health_marks_local_db_mock_seed() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["data_source"]["mode"] == "local-db"
    assert payload["data_source"]["seed"] == "mock"
    assert payload["data_source"]["is_real_workflow"] is False


def test_reports_are_read_from_local_db_seed() -> None:
    response = client.get("/api/reports")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data_source"]["mode"] == "local-db"
    assert payload["data_source"]["seed"] == "mock"
    assert payload["items"]
    assert any(item["id"].startswith("mock-") for item in payload["items"])


def test_report_detail_includes_mechanism_objects() -> None:
    response = client.get("/api/reports/mock-001")

    assert response.status_code == 200
    item = response.json()["item"]
    assert item["claims"]
    assert item["evidence"]
    assert item["qa_gate"]["verdict"] in {"pass", "rework"}
    assert item["trace_steps"]


def test_analysis_pack_endpoint_includes_qa_preview() -> None:
    response = client.get("/api/reports/mock-001/analysis-pack")

    assert response.status_code == 200
    item = response.json()["item"]
    assert item["analysis_pack"]["claim_evidence_map"]
    assert item["qa_preview"]["verdict"] in {"pass", "rework"}
