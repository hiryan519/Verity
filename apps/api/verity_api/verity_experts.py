from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4
import time

from .analysis import build_analysis_pack
from .db import (
    increment_memory_applied,
    increment_memory_trial,
    list_active_memories_for_agent,
    list_candidate_memories_for_agent,
)
from .qa import run_qa_gate


@dataclass(frozen=True)
class VerityExpert:
    id: str
    name: str
    layer: str
    goal: str
    tool_scope: tuple[str, ...]
    output_schema: str
    depends_on: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "tool_scope": list(self.tool_scope),
            "depends_on": list(self.depends_on),
        }


@dataclass
class ExpertRunResult:
    expert_id: str
    expert_name: str
    status: str
    started_at: float
    ended_at: float
    output: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    trace: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_ms(self) -> int:
        return int((self.ended_at - self.started_at) * 1000)

    def to_dict(self) -> dict[str, Any]:
        return {
            "expert_id": self.expert_id,
            "expert_name": self.expert_name,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "output": self.output,
            "error": self.error,
            "trace": self.trace,
        }


VERITY_EXPERTS: dict[str, VerityExpert] = {
    "research_orchestrator": VerityExpert(
        id="research_orchestrator",
        name="Research Orchestrator",
        layer="orchestration",
        goal="理解研究目标，拆解专家任务，管理执行状态并汇总结果。",
        tool_scope=("expert_router", "workflow_plan", "trace_write"),
        output_schema="research_plan",
    ),
    "evidence_collector": VerityExpert(
        id="evidence_collector",
        name="Evidence Collector",
        layer="execution",
        goal="从允许的数据源中整理可复查证据，并标注来源与风险。",
        tool_scope=("local_db_read", "evidence_scoring", "trace_write"),
        output_schema="evidence_items",
    ),
    "product_analyst": VerityExpert(
        id="product_analyst",
        name="Product Analyst",
        layer="analysis",
        goal="分析产品定位、核心场景和功能边界。",
        tool_scope=("local_db_read", "claim_draft", "trace_write"),
        output_schema="claims",
    ),
    "business_pricing_analyst": VerityExpert(
        id="business_pricing_analyst",
        name="Business / Pricing Analyst",
        layer="analysis",
        goal="分析定价、套餐边界和商业模式线索。",
        tool_scope=("local_db_read", "claim_draft", "trace_write"),
        output_schema="claims",
    ),
    "cross_validator": VerityExpert(
        id="cross_validator",
        name="Cross-validation Agent",
        layer="validation",
        goal="检查 claim-evidence 绑定、冲突和数据缺口。",
        tool_scope=("analysis_pack_read", "conflict_check", "trace_write"),
        output_schema="analysis_pack_review",
        depends_on=("evidence_collector", "product_analyst", "business_pricing_analyst"),
    ),
    "qa_agent": VerityExpert(
        id="qa_agent",
        name="QA Agent",
        layer="quality_gate",
        goal="在报告生成前对 Analysis Pack 执行质量门控。",
        tool_scope=("qa_gate", "trace_write"),
        output_schema="qa_gate_result",
        depends_on=("cross_validator",),
    ),
    "report_writer": VerityExpert(
        id="report_writer",
        name="Report Writer Agent",
        layer="delivery",
        goal="仅基于通过质检或带风险提示的 Analysis Pack 生成报告草案。",
        tool_scope=("analysis_pack_read", "report_draft", "trace_write"),
        output_schema="report_sections",
        depends_on=("qa_agent",),
    ),
}


READ_ONLY_PARALLEL_EXPERTS = ("evidence_collector", "product_analyst", "business_pricing_analyst")


class VerityExpertRunner:
    """Verity expert wrapper.

    It does not expose Evolva's default role names as product experts. The first
    implementation is deterministic and local-db backed so that P3 can validate
    orchestration, parallel execution, traceability, and Analysis Pack assembly
    before real workflow execution is wired in.
    """

    def list_experts(self) -> list[dict[str, Any]]:
        return [expert.to_dict() for expert in VERITY_EXPERTS.values()]

    def route(self, research_goal: str) -> dict[str, Any]:
        selected = [
            "research_orchestrator",
            *READ_ONLY_PARALLEL_EXPERTS,
            "cross_validator",
            "qa_agent",
            "report_writer",
        ]
        return {
            "run_id": f"expert_run_{uuid4().hex[:8]}",
            "research_goal": research_goal,
            "selected_experts": selected,
            "parallel_groups": [list(READ_ONLY_PARALLEL_EXPERTS)],
            "sequential_tail": ["cross_validator", "qa_agent", "report_writer"],
            "boundary": "deterministic local-db wrapper; not real online collection",
        }

    def run_minimal_research(
        self,
        *,
        report_id: str,
        research_goal: str,
        claims: list[dict[str, Any]],
        evidence_items: list[dict[str, Any]],
        dimensions: list[str],
    ) -> dict[str, Any]:
        route = self.route(research_goal)
        results: list[ExpertRunResult] = []

        results.append(self._run_single("research_orchestrator", route, claims=claims, evidence_items=evidence_items))

        with ThreadPoolExecutor(max_workers=len(READ_ONLY_PARALLEL_EXPERTS)) as executor:
            futures = {
                executor.submit(self._run_single, expert_id, route, claims=claims, evidence_items=evidence_items): expert_id
                for expert_id in READ_ONLY_PARALLEL_EXPERTS
            }
            for future in as_completed(futures):
                results.append(future.result())

        analysis_pack = build_analysis_pack(report_id, research_goal, dimensions, claims, evidence_items)
        results.append(self._run_single("cross_validator", route, analysis_pack=analysis_pack))

        qa_result = run_qa_gate(analysis_pack)
        results.append(self._run_single("qa_agent", route, analysis_pack=analysis_pack, qa_result=qa_result))
        results.append(self._run_single("report_writer", route, analysis_pack=analysis_pack, qa_result=qa_result))

        return {
            "run_id": route["run_id"],
            "report_id": report_id,
            "research_goal": research_goal,
            "route": route,
            "expert_results": [result.to_dict() for result in results],
            "analysis_pack": analysis_pack,
            "qa_gate": qa_result,
            "parallel_experts": list(READ_ONLY_PARALLEL_EXPERTS),
            "is_real_workflow": False,
            "boundary": "P3.3 validates expert orchestration over local-db seed data; it is not real online research.",
        }

    def _run_single(self, expert_id: str, route: dict[str, Any], **context: Any) -> ExpertRunResult:
        expert = VERITY_EXPERTS[expert_id]
        started = time.time()
        active_memories = list_active_memories_for_agent(expert_id)
        candidate_memories = list_candidate_memories_for_agent(expert_id)
        try:
            output = _deterministic_expert_output(expert, context, active_memories, candidate_memories)
            increment_memory_applied([memory["id"] for memory in active_memories])
            increment_memory_trial([memory["id"] for memory in candidate_memories])
            status = "done"
            error = ""
        except Exception as exc:
            output = {}
            status = "failed"
            error = str(exc)
        ended = time.time()
        return ExpertRunResult(
            expert_id=expert.id,
            expert_name=expert.name,
            status=status,
            started_at=started,
            ended_at=ended,
            output=output,
            error=error,
            trace={
                "run_id": route["run_id"],
                "stage": expert.layer,
                "task": expert.goal,
                "tool_scope": list(expert.tool_scope),
                "output_schema": expert.output_schema,
                "depends_on": list(expert.depends_on),
                "applied_memory_ids": [memory["id"] for memory in active_memories],
                "candidate_memory_ids": [memory["id"] for memory in candidate_memories],
            },
        )


def _deterministic_expert_output(
    expert: VerityExpert,
    context: dict[str, Any],
    active_memories: list[dict[str, Any]],
    candidate_memories: list[dict[str, Any]],
) -> dict[str, Any]:
    claims = context.get("claims", [])
    evidence_items = context.get("evidence_items", [])
    analysis_pack = context.get("analysis_pack", {})
    qa_result = context.get("qa_result", {})
    memory_payload = {
        "applied_memories": [
            {
                "id": memory["id"],
                "type": memory["memory_type"],
                "content": memory["content"],
                "influence_target": memory["influence_target"],
                "effect_strategy": memory["effect_strategy"],
            }
            for memory in active_memories
        ],
        "checklist_additions": [memory["content"] for memory in active_memories if memory["influence_target"] == "agent_checklist"],
        "candidate_suggestions": [
            {
                "id": memory["id"],
                "content": memory["content"],
                "effect_strategy": memory["effect_strategy"],
                "source": memory["source_type"],
                "note": "Candidate trial only; do not use as fact evidence.",
            }
            for memory in candidate_memories
        ],
    }

    if expert.id == "research_orchestrator":
        return {
            "plan": [
                "confirm_scope",
                "parallel_read_only_research",
                "cross_validation",
                "qa_gate",
                "report_writer",
            ],
            "selected_experts": list(VERITY_EXPERTS),
            **memory_payload,
        }
    if expert.id == "evidence_collector":
        return {
            "evidence_count": len(evidence_items),
            "high_confidence_count": sum(1 for item in evidence_items if item.get("confidence_level") == "high"),
            "risk_notes": [item.get("risk_note", "") for item in evidence_items if item.get("risk_note")],
            **memory_payload,
        }
    if expert.id == "product_analyst":
        product_claims = [claim for claim in claims if claim.get("dimension") in {"产品定位", "核心场景"}]
        return {"claims": product_claims, "claim_count": len(product_claims), **memory_payload}
    if expert.id == "business_pricing_analyst":
        pricing_claims = [claim for claim in claims if claim.get("dimension") in {"定价策略", "商业模式"}]
        return {
            "claims": pricing_claims,
            "claim_count": len(pricing_claims),
            "data_gap": "定价策略缺少可用结论" if not pricing_claims else "",
            **memory_payload,
        }
    if expert.id == "cross_validator":
        return {
            "claim_evidence_map": analysis_pack.get("claim_evidence_map", []),
            "data_gaps": analysis_pack.get("data_gaps", []),
            "conflicts": analysis_pack.get("conflicts", []),
            **memory_payload,
        }
    if expert.id == "qa_agent":
        return {**qa_result, **memory_payload}
    if expert.id == "report_writer":
        return {
            "allowed_to_write_without_risk": qa_result.get("verdict") == "pass",
            "required_risk_notes": qa_result.get("issues", []),
            "source": "analysis_pack_only",
            **memory_payload,
        }
    return {}
