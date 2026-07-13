from __future__ import annotations

from dataclasses import asdict, dataclass
import os
from typing import Any

from .expert_context import build_expert_context_from_db
from .expert_execution_contracts import get_execution_contract
from .expert_registry import get_expert_contract


@dataclass(frozen=True)
class LLMProviderStatus:
    available: bool
    provider: str
    model: str
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


def get_llm_provider_status() -> dict:
    provider = os.getenv("VERITY_LLM_PROVIDER", "").strip() or _infer_provider()
    model = os.getenv("VERITY_LLM_MODEL", "").strip() or _default_model(provider)
    key = _api_key_for(provider)

    if not provider:
        return LLMProviderStatus(
            available=False,
            provider="",
            model="",
            reason="provider_not_configured",
        ).to_dict()
    if not key:
        return LLMProviderStatus(
            available=False,
            provider=provider,
            model=model,
            reason="api_key_not_configured",
        ).to_dict()
    return LLMProviderStatus(available=True, provider=provider, model=model, reason="ready").to_dict()


def prepare_llm_expert_execution(expert_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    expert_contract = get_expert_contract(expert_id)
    execution_contract = get_execution_contract(expert_id)
    provider_status = get_llm_provider_status()

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


def _default_model(provider: str) -> str:
    if provider == "zhipu":
        return "glm-5-turbo"
    if provider == "openai":
        return "gpt-5-mini"
    return ""
