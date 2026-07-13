from fastapi.testclient import TestClient

from verity_api.main import app


client = TestClient(app)


def test_llm_status_reports_not_configured_without_provider(monkeypatch) -> None:
    monkeypatch.delenv("VERITY_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("VERITY_LLM_API_KEY", raising=False)
    monkeypatch.delenv("ZHIPUAI_API_KEY", raising=False)
    monkeypatch.delenv("GLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.get("/api/llm/status")

    assert response.status_code == 200
    item = response.json()["item"]
    assert item["available"] is False
    assert item["reason"] == "provider_not_configured"


def test_llm_prepare_does_not_fallback_to_mock_when_provider_missing(monkeypatch) -> None:
    monkeypatch.setenv("VERITY_LLM_PROVIDER", "zhipu")
    monkeypatch.delenv("ZHIPUAI_API_KEY", raising=False)
    monkeypatch.delenv("GLM_API_KEY", raising=False)

    response = client.post(
        "/api/llm/experts/product_analyst/prepare",
        json={"input_payload": {"research_goal": "分析 A 与 B"}},
    )

    assert response.status_code == 200
    item = response.json()["item"]
    assert item["available"] is False
    assert item["status"] == "blocked"
    assert item["reason"] == "api_key_not_configured"
    assert item["is_real_llm_execution"] is False
    assert item["mock_fallback_used"] is False


def test_llm_prepare_binds_registry_contract_context_and_provider(monkeypatch) -> None:
    monkeypatch.setenv("VERITY_LLM_PROVIDER", "zhipu")
    monkeypatch.setenv("ZHIPUAI_API_KEY", "test-key")
    monkeypatch.setenv("VERITY_LLM_MODEL", "glm-5-turbo")

    response = client.post(
        "/api/llm/experts/report_writer/prepare",
        json={"input_payload": {"report_outline": {"sections": []}}},
    )

    assert response.status_code == 200
    item = response.json()["item"]
    assert item["available"] is True
    assert item["status"] == "ready"
    assert item["reason"] == "provider_ready_execution_not_started"
    assert item["provider_status"]["provider"] == "zhipu"
    assert item["provider_status"]["model"] == "glm-5-turbo"
    assert item["expert_contract"]["id"] == "report_writer"
    assert item["execution_contract"]["expert_id"] == "report_writer"
    assert item["runtime_context"]["context_policy"]["not_evidence"] is True
    assert item["mock_fallback_used"] is False


def test_llm_prepare_unknown_expert_is_blocked(monkeypatch) -> None:
    monkeypatch.setenv("VERITY_LLM_PROVIDER", "zhipu")
    monkeypatch.setenv("ZHIPUAI_API_KEY", "test-key")

    response = client.post("/api/llm/experts/not_real/prepare", json={"input_payload": {}})

    assert response.status_code == 200
    item = response.json()["item"]
    assert item["available"] is False
    assert item["status"] == "blocked"
    assert item["reason"] == "expert_contract_not_found"
