from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal
from uuid import uuid4

from .expert_registry import get_expert_contract


SplitReason = Literal["within_budget", "token_budget", "unit_count", "forced_single"]


@dataclass(frozen=True)
class WorkUnit:
    id: str
    topic: str
    token_estimate: int = 0
    evidence_ids: tuple[str, ...] = ()
    claim_ids: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "WorkUnit":
        return cls(
            id=payload["id"],
            topic=payload.get("topic", payload["id"]),
            token_estimate=int(payload.get("token_estimate", 0)),
            evidence_ids=tuple(payload.get("evidence_ids", ())),
            claim_ids=tuple(payload.get("claim_ids", ())),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "topic": self.topic,
            "token_estimate": self.token_estimate,
            "evidence_ids": list(self.evidence_ids),
            "claim_ids": list(self.claim_ids),
        }


@dataclass
class ExpertInstancePlan:
    instance_id: str
    expert_id: str
    batch_index: int
    scope: str
    work_units: list[WorkUnit] = field(default_factory=list)
    split_reason: SplitReason = "within_budget"

    @property
    def token_estimate(self) -> int:
        return sum(unit.token_estimate for unit in self.work_units)

    def to_dict(self) -> dict[str, Any]:
        evidence_ids: list[str] = []
        claim_ids: list[str] = []
        for unit in self.work_units:
            evidence_ids.extend(unit.evidence_ids)
            claim_ids.extend(unit.claim_ids)
        return {
            "instance_id": self.instance_id,
            "expert_id": self.expert_id,
            "batch_index": self.batch_index,
            "scope": self.scope,
            "split_reason": self.split_reason,
            "token_estimate": self.token_estimate,
            "work_units": [unit.to_dict() for unit in self.work_units],
            "evidence_ids": sorted(set(evidence_ids)),
            "claim_ids": sorted(set(claim_ids)),
        }


def plan_expert_instances(
    *,
    expert_id: str,
    work_units: list[dict[str, Any]],
    token_budget: int,
    max_units_per_instance: int = 6,
    force_single: bool = False,
) -> list[dict[str, Any]]:
    expert = get_expert_contract(expert_id)
    if expert is None:
        raise ValueError(f"Unknown expert_id: {expert_id}")

    units = [WorkUnit.from_dict(unit) for unit in work_units]
    if force_single or not expert["supports_multi_instance"] or len(units) <= 1:
        return [
            ExpertInstancePlan(
                instance_id=_instance_id(expert_id),
                expert_id=expert_id,
                batch_index=1,
                scope=_scope_for(units),
                work_units=units,
                split_reason="forced_single" if force_single or not expert["supports_multi_instance"] else "within_budget",
            ).to_dict()
        ]

    plans: list[ExpertInstancePlan] = []
    current: list[WorkUnit] = []
    current_tokens = 0
    split_reason: SplitReason = "within_budget"

    for unit in units:
        would_exceed_tokens = current and current_tokens + unit.token_estimate > token_budget
        would_exceed_units = current and len(current) >= max_units_per_instance
        if would_exceed_tokens or would_exceed_units:
            plans.append(
                ExpertInstancePlan(
                    instance_id=_instance_id(expert_id),
                    expert_id=expert_id,
                    batch_index=len(plans) + 1,
                    scope=_scope_for(current),
                    work_units=current,
                    split_reason="token_budget" if would_exceed_tokens else "unit_count",
                )
            )
            split_reason = "token_budget" if would_exceed_tokens else "unit_count"
            current = []
            current_tokens = 0

        current.append(unit)
        current_tokens += unit.token_estimate

    if current:
        plans.append(
            ExpertInstancePlan(
                instance_id=_instance_id(expert_id),
                expert_id=expert_id,
                batch_index=len(plans) + 1,
                scope=_scope_for(current),
                work_units=current,
                split_reason=split_reason,
            )
        )

    return [plan.to_dict() for plan in plans]


def merge_instance_fragments(
    *,
    expert_id: str,
    fragments: list[dict[str, Any]],
    output_pack_type: str,
) -> dict[str, Any]:
    merged_claims: list[dict[str, Any]] = []
    merged_data_gaps: list[str] = []
    merged_risks: list[str] = []
    evidence_ids: set[str] = set()
    claim_ids: set[str] = set()
    fragment_index: list[dict[str, Any]] = []

    for fragment in fragments:
        instance_id = fragment["instance_id"]
        output = fragment.get("output", {})
        merged_claims.extend(output.get("claims", []))
        merged_data_gaps.extend(output.get("data_gaps", []))
        merged_risks.extend(output.get("risk_notes", []))
        evidence_ids.update(fragment.get("evidence_ids", []))
        claim_ids.update(fragment.get("claim_ids", []))
        fragment_index.append(
            {
                "instance_id": instance_id,
                "scope": fragment.get("scope", ""),
                "merge_reason": "merged_same_expert_fragment",
                "evidence_ids": fragment.get("evidence_ids", []),
                "claim_ids": fragment.get("claim_ids", []),
            }
        )

    return {
        "expert_id": expert_id,
        "pack_type": output_pack_type,
        "fragment_count": len(fragments),
        "claims": merged_claims,
        "data_gaps": _dedupe(merged_data_gaps),
        "risk_notes": _dedupe(merged_risks),
        "evidence_ids": sorted(evidence_ids),
        "claim_ids": sorted(claim_ids),
        "fragment_index": fragment_index,
        "merge_policy": "preserve_traceability_and_risks",
    }


def _instance_id(expert_id: str) -> str:
    return f"{expert_id}_{uuid4().hex[:8]}"


def _scope_for(units: list[WorkUnit]) -> str:
    if not units:
        return "empty"
    topics = [unit.topic for unit in units]
    if len(topics) == 1:
        return topics[0]
    return f"{topics[0]} 等 {len(topics)} 个工作单元"


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))
