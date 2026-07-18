from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
import re
import time
from typing import Any, Callable
from uuid import uuid4

import httpx

from .expert_context import build_expert_context_from_db
from .expert_execution_contracts import get_execution_contract
from .expert_registry import get_expert_contract


EXPERT_MODEL_TIERS = {
    "research_orchestrator": "reasoning",
    "evidence_collector": "fast",
    "product_analyst": "fast",
    "pricing_analyst": "fast",
    "user_experience_analyst": "fast",
    "cross_validator": "reasoning",
    "qa_agent": "reasoning",
    "report_writer": "reasoning",
}


class LLMProviderError(RuntimeError):
    """A provider failure that can be returned without exposing response secrets."""

    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


@dataclass(frozen=True)
class LLMProviderStatus:
    available: bool
    provider: str
    model: str
    reason: str
    model_tier: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class OpenAICompatibleProvider:
    """Minimal chat-completions adapter for OpenAI-compatible providers.

    The adapter only requests JSON and never logs or returns the API key.
    A custom httpx transport keeps the boundary unit-testable without a live key.
    """

    def __init__(
        self,
        *,
        provider: str,
        api_key: str,
        model: str,
        base_url: str,
        timeout_seconds: float = 90.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.provider = provider
        self.model = model
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=timeout_seconds,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def complete_json(
        self,
        *,
        system_prompt: str,
        input_payload: dict[str, Any],
        max_tokens: int,
    ) -> dict[str, Any]:
        # DeepSeek's JSON Output mode requires the prompt to explicitly mention
        # json. Keep this provider-compatible instruction at the adapter boundary
        # instead of duplicating it in every expert contract.
        system_prompt = (
            f"{system_prompt.rstrip()}\n\n"
            "Output only a valid JSON object (json), with no Markdown fences or extra text."
        )
        request_payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": json.dumps(input_payload, ensure_ascii=False, separators=(",", ":")),
                },
            ],
            "temperature": 0.1,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }

        try:
            response = self._client.post("/chat/completions", json=request_payload)
        except httpx.TimeoutException as exc:
            raise LLMProviderError("provider_timeout", "LLM provider request timed out.", retryable=True) from exc
        except httpx.HTTPError as exc:
            raise LLMProviderError("provider_network_error", "LLM provider request failed.", retryable=True) from exc

        if response.status_code >= 500:
            raise LLMProviderError("provider_server_error", "LLM provider returned a server error.", retryable=True)
        if response.status_code >= 400:
            raise LLMProviderError("provider_request_error", "LLM provider rejected the request.")

        try:
            body = response.json()
            content = body["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError("provider_response_invalid", "LLM provider returned an invalid response.") from exc

        parsed = _parse_json_object(content)
        usage = body.get("usage") if isinstance(body.get("usage"), dict) else {}
        return {
            "output": parsed,
            "usage": usage,
            "provider_response_id": body.get("id", ""),
        }


def get_llm_provider_status(expert_id: str | None = None) -> dict:
    provider = os.getenv("VERITY_LLM_PROVIDER", "").strip() or _infer_provider()
    model_tier = EXPERT_MODEL_TIERS.get(expert_id or "", "")
    model = _model_for_expert(provider, expert_id)
    key = _api_key_for(provider)

    if not provider:
        return LLMProviderStatus(
            available=False,
            provider="",
            model="",
            reason="provider_not_configured",
            model_tier=model_tier,
        ).to_dict()
    if not key:
        return LLMProviderStatus(
            available=False,
            provider=provider,
            model=model,
            reason="api_key_not_configured",
            model_tier=model_tier,
        ).to_dict()
    if not model:
        return LLMProviderStatus(
            available=False,
            provider=provider,
            model="",
            reason="model_not_configured",
            model_tier=model_tier,
        ).to_dict()
    return LLMProviderStatus(
        available=True,
        provider=provider,
        model=model,
        reason="ready",
        model_tier=model_tier,
    ).to_dict()


def prepare_llm_expert_execution(expert_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    expert_contract = get_expert_contract(expert_id)
    execution_contract = get_execution_contract(expert_id)
    provider_status = get_llm_provider_status(expert_id)

    if expert_contract is None or execution_contract is None:
        return {
            "available": False,
            "status": "blocked",
            "reason": "expert_contract_not_found",
            "expert_id": expert_id,
            "is_real_llm_execution": False,
        }

    context = build_expert_context_from_db(expert_id)
    request_payload = payload or {}
    base = {
        "expert_id": expert_id,
        "expert_contract": expert_contract,
        "execution_contract": execution_contract,
        "runtime_context": context,
        "input_payload_keys": sorted(request_payload),
        "model_tier": EXPERT_MODEL_TIERS.get(expert_id, ""),
        "is_real_llm_execution": False,
        "mock_fallback_used": False,
    }

    if not provider_status["available"]:
        return {
            **base,
            "available": False,
            "status": "blocked",
            "reason": provider_status["reason"],
            "provider_status": provider_status,
        }

    return {
        **base,
        "available": True,
        "status": "ready",
        "reason": "provider_ready_execution_not_started",
        "provider_status": provider_status,
    }


def execute_llm_expert(
    expert_id: str,
    payload: dict[str, Any] | None = None,
    *,
    provider_factory: Callable[[dict[str, Any]], OpenAICompatibleProvider] | None = None,
) -> dict[str, Any]:
    """Execute one governed expert and return a traceable structured result.

    This endpoint intentionally stops at one expert invocation. Workflow orchestration,
    evidence routing, QA Gate and report persistence remain the caller's responsibility.
    """

    request_payload = payload or {}
    prepared = prepare_llm_expert_execution(expert_id, request_payload)
    if not prepared["available"]:
        return prepared

    execution_contract = prepared["execution_contract"]
    provider_status = prepared["provider_status"]
    started = time.perf_counter()
    provider = provider_factory(provider_status) if provider_factory else _provider_from_status(provider_status)
    response: dict[str, Any] | None = None
    error: dict[str, Any] | None = None

    try:
        response = provider.complete_json(
            system_prompt=_prompt_with_output_schema(execution_contract),
            input_payload=request_payload,
            max_tokens=_max_output_tokens(expert_id),
        )
        output = response["output"]
        validation_errors = _validate_output(execution_contract, output)
        if validation_errors:
            error = {
                "code": "structured_output_invalid",
                "message": "LLM output did not satisfy the expert output contract.",
                "details": validation_errors,
            }
            status = "failed"
        else:
            status = "completed"
    except LLMProviderError as exc:
        output = {}
        error = {"code": exc.code, "message": str(exc), "retryable": exc.retryable}
        status = "failed"
    finally:
        provider.close()

    duration_ms = int((time.perf_counter() - started) * 1000)
    usage = response.get("usage", {}) if response else {}
    trace_step = _build_trace_step(
        expert_id=expert_id,
        payload=request_payload,
        output=output,
        error=error,
        status=status,
        model=provider_status["model"],
        usage=usage,
        duration_ms=duration_ms,
    )

    report_id = request_payload.get("report_id")
    if report_id:
        _append_trace_step(report_id, trace_step)

    return {
        "available": True,
        "status": status,
        "reason": "completed" if status == "completed" else error["code"],
        "expert_id": expert_id,
        "provider_status": provider_status,
        "is_real_llm_execution": status == "completed",
        "mock_fallback_used": False,
        "output": output,
        "error": error,
        "trace_step": trace_step,
    }


def _provider_from_status(status: dict[str, Any]) -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(
        provider=status["provider"],
        api_key=_api_key_for(status["provider"]),
        model=status["model"],
        base_url=_base_url_for(status["provider"]),
        timeout_seconds=float(os.getenv("VERITY_LLM_TIMEOUT_SECONDS", "90")),
    )


def _infer_provider() -> str:
    if os.getenv("ZHIPUAI_API_KEY") or os.getenv("GLM_API_KEY"):
        return "zhipu"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    return ""


def _api_key_for(provider: str) -> str:
    if provider == "zhipu":
        return os.getenv("ZHIPUAI_API_KEY", "") or os.getenv("GLM_API_KEY", "")
    if provider == "openai":
        return os.getenv("OPENAI_API_KEY", "")
    if provider:
        return os.getenv("VERITY_LLM_API_KEY", "")
    return ""


def _base_url_for(provider: str) -> str:
    configured = os.getenv("VERITY_LLM_BASE_URL", "").strip()
    if configured:
        return configured
    if provider == "zhipu":
        return "https://open.bigmodel.cn/api/paas/v4"
    if provider == "openai":
        return "https://api.openai.com/v1"
    return ""


def _default_model(provider: str) -> str:
    if provider == "zhipu":
        return "glm-5-turbo"
    if provider == "openai":
        return "gpt-5-mini"
    return ""


def _model_for_expert(provider: str, expert_id: str | None) -> str:
    if expert_id:
        specific = os.getenv(f"VERITY_LLM_MODEL_{expert_id.upper()}", "").strip()
        if specific:
            return specific
        tier = EXPERT_MODEL_TIERS.get(expert_id, "")
        tier_model = os.getenv(f"VERITY_LLM_MODEL_{tier.upper()}", "").strip() if tier else ""
        if tier_model:
            return tier_model
    return os.getenv("VERITY_LLM_MODEL", "").strip() or _default_model(provider)


def _max_output_tokens(expert_id: str) -> int:
    value = os.getenv(f"VERITY_LLM_MAX_TOKENS_{expert_id.upper()}", "").strip()
    if value.isdigit():
        return max(256, int(value))
    return int(os.getenv("VERITY_LLM_MAX_TOKENS", "3000"))


def _prompt_with_output_schema(contract: dict[str, Any]) -> str:
    required_fields = [
        field["name"]
        for field in contract.get("output_schema", [])
        if field.get("required")
    ]
    field_text = ", ".join(required_fields) or "the declared fields"
    return (
        f"{contract['prompt_fragment'].rstrip()}\n\n"
        "Return one JSON object using the exact top-level field names from the contract. "
        f"Required fields: {field_text}. Use an empty array when a required list has no items. "
        "Do not rename fields or add Markdown fences."
    )


def _parse_json_object(content: Any) -> dict[str, Any]:
    if isinstance(content, list):
        content = "".join(
            block.get("text", "") for block in content if isinstance(block, dict) and isinstance(block.get("text"), str)
        )
    if not isinstance(content, str):
        raise LLMProviderError("structured_output_invalid", "LLM content was not text.")
    candidate = content.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", candidate, re.DOTALL | re.IGNORECASE)
    if fenced:
        candidate = fenced.group(1)
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise LLMProviderError("structured_output_invalid", "LLM output was not valid JSON.") from exc
    if not isinstance(parsed, dict):
        raise LLMProviderError("structured_output_invalid", "LLM output must be a JSON object.")
    return parsed


def _validate_output(contract: dict[str, Any], output: Any) -> list[str]:
    if not isinstance(output, dict):
        return ["output_not_object"]
    errors: list[str] = []
    for field in contract["output_schema"]:
        name = field["name"]
        if field.get("required") and name not in output:
            errors.append(f"missing_required_field:{name}")
            continue
        if name in output and not _matches_schema_type(output[name], field["type"]):
            errors.append(f"invalid_field_type:{name}:{field['type']}")
    return errors


def _matches_schema_type(value: Any, field_type: str) -> bool:
    if field_type == "array":
        return isinstance(value, list)
    if field_type == "object":
        return isinstance(value, dict)
    if field_type == "string":
        return isinstance(value, str)
    if field_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if field_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if field_type == "boolean":
        return isinstance(value, bool)
    return True


def _build_trace_step(
    *,
    expert_id: str,
    payload: dict[str, Any],
    output: dict[str, Any],
    error: dict[str, Any] | None,
    status: str,
    model: str,
    usage: dict[str, Any],
    duration_ms: int,
) -> dict[str, Any]:
    expert = get_expert_contract(expert_id) or {}
    return {
        "id": f"llm-{uuid4().hex[:12]}",
        "stage": "llm_expert_execution",
        "agent": expert.get("name", expert_id),
        "task": expert.get("responsibility", "") if expert else expert_id,
        "status": status,
        "model": model,
        "prompt": (get_execution_contract(expert_id) or {}).get("prompt_fragment", ""),
        "input": _redact(payload),
        "output": _redact(output if status == "completed" else {"error": error or {}}),
        "token_count": int(usage.get("total_tokens", 0) or 0),
        "duration_ms": duration_ms,
        "evidence_ids": payload.get("evidence_ids", []),
        "report_sections": payload.get("report_sections", []),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def _append_trace_step(report_id: str, trace_step: dict[str, Any]) -> None:
    from .db import append_trace_step

    append_trace_step(report_id, trace_step)


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            lowered = str(key).lower()
            result[key] = "[REDACTED]" if any(marker in lowered for marker in ("api_key", "token", "secret", "authorization")) else _redact(item)
        return result
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value
