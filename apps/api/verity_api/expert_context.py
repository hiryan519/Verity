from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .db import list_active_memories_for_agent, list_candidate_memories_for_agent


@dataclass(frozen=True)
class MountedSkill:
    skill_id: str
    name: str
    version: str
    summary: str
    target_expert: str
    status: str = "mounted"

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MountedSkill":
        return cls(
            skill_id=payload["skill_id"],
            name=payload["name"],
            version=payload["version"],
            summary=payload["summary"],
            target_expert=payload["target_expert"],
            status=payload.get("status", "mounted"),
        )

    def to_context(self) -> dict[str, str]:
        return asdict(self)


def build_expert_context_from_db(expert_id: str, mounted_skills: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return build_expert_context(
        expert_id=expert_id,
        active_memories=list_active_memories_for_agent(expert_id),
        candidate_memories=list_candidate_memories_for_agent(expert_id),
        mounted_skills=mounted_skills or [],
    )


def build_expert_context(
    *,
    expert_id: str,
    active_memories: list[dict[str, Any]],
    candidate_memories: list[dict[str, Any]],
    mounted_skills: list[dict[str, Any]],
) -> dict[str, Any]:
    active_context = [_active_memory_to_context(memory) for memory in active_memories if memory.get("target_agent") == expert_id]
    candidate_context = [_candidate_memory_to_context(memory) for memory in candidate_memories if memory.get("target_agent") == expert_id]
    skill_context = [
        skill.to_context()
        for skill in (_safe_skill(payload) for payload in mounted_skills)
        if skill is not None and skill.target_expert == expert_id and skill.status == "mounted"
    ]

    return {
        "expert_id": expert_id,
        "checklist_context": active_context,
        "trial_hints": candidate_context,
        "mounted_skills": skill_context,
        "context_policy": {
            "active_memory_use": "method_or_checklist_context_only",
            "candidate_memory_use": "low_weight_trial_hint_only",
            "skill_use": "versioned_mounted_methods_only",
            "not_evidence": True,
        },
    }


def _active_memory_to_context(memory: dict[str, Any]) -> dict[str, Any]:
    return {
        "memory_id": memory["id"],
        "content": memory["content"],
        "effect_strategy": memory.get("effect_strategy") or memory.get("influence_target"),
        "source_type": memory.get("source_type", ""),
        "not_fact_evidence": True,
    }


def _candidate_memory_to_context(memory: dict[str, Any]) -> dict[str, Any]:
    return {
        "memory_id": memory["id"],
        "content": memory["content"],
        "effect_strategy": memory.get("effect_strategy") or memory.get("influence_target"),
        "source_type": memory.get("source_type", ""),
        "trial_policy": "low_weight_target_expert_only",
        "not_fact_evidence": True,
        "risk_note": "Candidate memory is a trial hint and must not support factual claims.",
    }


def _safe_skill(payload: dict[str, Any]) -> MountedSkill | None:
    required = {"skill_id", "name", "version", "summary", "target_expert"}
    if required - set(payload):
        return None
    if not str(payload["version"]).startswith("v"):
        return None
    return MountedSkill.from_dict(payload)
