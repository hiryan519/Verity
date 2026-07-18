from fastapi.testclient import TestClient
import httpx

from verity_api.main import app
from verity_api.llm_execution import OpenAICompatibleProvider, execute_llm_expert


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


def test_openai_compatible_provider_sends_json_request_without_live_network() -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["authorization"] = request.headers["authorization"]
        captured["payload"] = request.read()
        return httpx.Response(
            200,
            json={
                "id": "response-1",
                "choices": [{"message": {"content": '{"claims": [], "data_gaps": [], "risk_notes": [], "comparison_items": []}'}}],
                "usage": {"total_tokens": 123},
            },
            request=request,
        )

    provider = OpenAICompatibleProvider(
        provider="test",
        api_key="test-secret",
        model="fast-model",
        base_url="https://provider.example/v1",
        transport=httpx.MockTransport(handler),
    )
    result = provider.complete_json(
        system_prompt="return JSON",
        input_payload={"research_goal": "分析 A 与 B"},
        max_tokens=500,
    )
    provider.close()

    assert captured["authorization"] == "Bearer test-secret"
    assert b'"model":"fast-model"' in captured["payload"]
    assert b'"response_format":{"type":"json_object"}' in captured["payload"]
    assert b"json" in captured["payload"].lower()
    assert result["output"]["claims"] == []
    assert result["usage"]["total_tokens"] == 123


def test_execute_routes_experts_to_tier_models_and_validates_output(monkeypatch) -> None:
    monkeypatch.setenv("VERITY_LLM_PROVIDER", "zhipu")
    monkeypatch.setenv("ZHIPUAI_API_KEY", "test-key")
    monkeypatch.delenv("VERITY_LLM_MODEL", raising=False)
    monkeypatch.setenv("VERITY_LLM_MODEL_FAST", "fast-model")
    monkeypatch.setenv("VERITY_LLM_MODEL_REASONING", "reasoning-model")
    captured = {}

    class FakeProvider:
        def __init__(self, status):
            captured["status"] = status

        def complete_json(self, **kwargs):
            captured["request"] = kwargs
            return {
                "output": {
                    "claims": [],
                    "data_gaps": [],
                    "risk_notes": [],
                    "comparison_items": [],
                },
                "usage": {"total_tokens": 42},
            }

        def close(self):
            captured["closed"] = True

    result = execute_llm_expert(
        "product_analyst",
        {"research_goal": "分析 A 与 B"},
        provider_factory=FakeProvider,
    )

    assert result["status"] == "completed"
    assert result["is_real_llm_execution"] is True
    assert result["provider_status"]["model"] == "fast-model"
    assert result["provider_status"]["model_tier"] == "fast"
    assert result["trace_step"]["token_count"] == 42
    assert captured["request"]["max_tokens"] >= 256
    assert captured["closed"] is True


def test_execute_rejects_missing_required_structured_fields(monkeypatch) -> None:
    monkeypatch.setenv("VERITY_LLM_PROVIDER", "zhipu")
    monkeypatch.setenv("ZHIPUAI_API_KEY", "test-key")
    monkeypatch.setenv("VERITY_LLM_MODEL", "test-model")

    class FakeProvider:
        def __init__(self, status):
            pass

        def complete_json(self, **kwargs):
            return {"output": {"claims": []}, "usage": {}}

        def close(self):
            pass

    result = execute_llm_expert(
        "product_analyst",
        {"research_goal": "分析 A 与 B"},
        provider_factory=FakeProvider,
    )

    assert result["status"] == "failed"
    assert result["reason"] == "structured_output_invalid"
    assert "missing_required_field:data_gaps" in result["error"]["details"]
    assert result["trace_step"]["status"] == "failed"
