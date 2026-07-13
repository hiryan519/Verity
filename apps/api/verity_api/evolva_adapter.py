from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evolva.agent.memory import MemoryStore
from evolva.agent.redaction import Redactor
from evolva.agent.skills import SkillStore
from evolva.agent.tracing import TraceRecorder
from evolva.config import AgentConfig

from .analysis import build_analysis_pack
from .db import persist_bounded_workflow_result, replace_trace_steps
from .qa import run_qa_gate
from .scoring import score_evidence


TRACE_STAGE_MAP = {
    "run_meta": "需求理解",
    "task_route": "编排派遣",
    "multi_agent_auto_route": "专家协作",
    "agent_chat_start": "需求理解",
    "tool_call": "工具调用",
    "tool_error": "工具调用",
    "policy_decision": "工具边界",
    "loop_start": "编排派遣",
    "loop_phase": "阶段执行",
    "loop_end": "汇总交付",
    "verity_adapter_smoke": "接入验证",
}


class EvolvaAdapter:
    """Read-only Verity adapter over Evolva runtime objects.

    The adapter intentionally wraps Evolva instead of changing its core runtime.
    It translates Evolva's infra-oriented trace/memory/skill objects into
    Verity's product-facing structures.
    """

    def __init__(self, root: Path | None = None):
        # The FastAPI process can start from apps/api; Evolva tools and workflow
        # fixtures must still resolve against the repository root.
        self.config = AgentConfig(root=root or REPO_ROOT)
        self.config.ensure_dirs()
        self.redactor = Redactor()

    def status(self) -> dict[str, Any]:
        trace_recorder = TraceRecorder(self.config.traces_dir, enabled=True, redactor=self.redactor)
        memory = MemoryStore(self.config.memory_file, context_min_confidence=self.config.memory_context_min_confidence)
        skills = SkillStore(self.config.skills_dir)
        trace_runs = trace_recorder.list_runs(limit=20)
        tools: list[str] = []
        llm_available = bool(self.config.api_key)
        dependency_warnings: list[str] = []
        try:
            from evolva.agent.core import EvolvaAgent

            agent = EvolvaAgent(self.config)
            tools = agent.tools.names()
            llm_available = agent.llm.available
        except ModuleNotFoundError as exc:
            dependency_warnings.append(f"Optional Evolva runtime dependency missing: {exc.name}")
        except Exception as exc:
            dependency_warnings.append(f"EvolvaAgent unavailable: {exc}")

        return {
            "available": True,
            "mode": "evolva-adapter",
            "root": str(self.config.root),
            "runtime_home": str(self.config.runtime_home),
            "llm_available": llm_available,
            "workflow_runs_dir": str(self.config.workflows_dir / "runs"),
            "traces_dir": str(self.config.traces_dir),
            "trace_runs": len(trace_runs),
            "memory": memory.audit(),
            "skills": skills.stats(),
            "tools": tools,
            "dependency_warnings": dependency_warnings,
            "notes": [
                "Adapter uses Evolva public runtime objects and does not modify Evolva core.",
                "Trace output is redacted before being exposed to Verity.",
                "Mock/local-db data remains separate from real Evolva runtime data.",
            ],
        }

    def list_traces(self, limit: int = 20) -> list[dict[str, Any]]:
        recorder = TraceRecorder(self.config.traces_dir, enabled=True, redactor=self.redactor)
        return recorder.list_runs(limit=limit)

    def load_trace(self, run_id: str) -> dict[str, Any]:
        recorder = TraceRecorder(self.config.traces_dir, enabled=True, redactor=self.redactor)
        return self.redactor.redact_json(recorder.load(run_id))

    def trace_to_verity_steps(self, run_id: str, *, report_id: str = "mock-001") -> list[dict[str, Any]]:
        trace = self.load_trace(run_id)
        started_at = float(trace.get("started_at") or 0)
        final_answer = str(trace.get("final_answer") or "")
        steps: list[dict[str, Any]] = []

        for index, event in enumerate(trace.get("events", []), start=1):
            data = event.get("data") or {}
            kind = str(event.get("kind") or "event")
            offset_ms = int((float(event.get("ts") or started_at) - started_at) * 1000) if started_at else 0
            agent = _agent_from_event(kind, data)
            status = _status_from_event(kind, data)
            task = _task_from_event(kind, data)
            output = _output_from_event(kind, data)

            steps.append(
                {
                    "id": f"{run_id}_{index:04d}",
                    "report_id": report_id,
                    "stage": TRACE_STAGE_MAP.get(kind, "执行事件"),
                    "agent": agent,
                    "task": task,
                    "status": status,
                    "model": str(data.get("model") or trace.get("summary", {}).get("model") or "unknown"),
                    "prompt": self.redactor.redact_text(str(data.get("prompt") or trace.get("user_input") or "")),
                    "input": self.redactor.redact_json(data.get("input") or data.get("args") or data),
                    "output": self.redactor.redact_json(output),
                    "token_count": _safe_int(data.get("token_count") or data.get("tokens") or data.get("usage_count"), 0),
                    "duration_ms": _safe_int(data.get("latency_ms"), offset_ms),
                    "evidence_ids": [],
                    "report_sections": [],
                    "created_at": time.strftime("%Y-%m-%dT%H:%M:%S+08:00", time.localtime(float(event.get("ts") or time.time()))),
                    "source": {
                        "runtime": "evolva",
                        "run_id": run_id,
                        "event_id": event.get("event_id", ""),
                        "kind": kind,
                    },
                }
            )

        if not steps and final_answer:
            steps.append(
                {
                    "id": f"{run_id}_final",
                    "report_id": report_id,
                    "stage": "汇总交付",
                    "agent": "EvolvaAgent",
                    "task": "Return final answer",
                    "status": str(trace.get("status") or "completed"),
                    "model": "unknown",
                    "prompt": self.redactor.redact_text(str(trace.get("user_input") or "")),
                    "input": {"user_input": self.redactor.redact_text(str(trace.get("user_input") or ""))},
                    "output": {"final_answer": self.redactor.redact_text(final_answer)},
                    "token_count": 0,
                    "duration_ms": int(trace.get("summary", {}).get("duration_ms") or 0),
                    "evidence_ids": [],
                    "report_sections": [],
                    "created_at": time.strftime("%Y-%m-%dT%H:%M:%S+08:00", time.localtime()),
                    "source": {"runtime": "evolva", "run_id": run_id, "event_id": "final", "kind": "final_answer"},
                }
            )

        return steps

    def create_smoke_trace(self) -> dict[str, Any]:
        recorder = TraceRecorder(self.config.traces_dir, enabled=True, redactor=self.redactor)
        run_id = recorder.start(
            "Verity P3 smoke trace: verify Evolva trace adapter without real competitor research.",
            meta={"runtime": "verity-adapter-smoke", "is_real_research": False},
        )
        recorder.event(
            "verity_adapter_smoke",
            {
                "task": "Map Evolva TraceRecorder event into Verity trace_steps",
                "input": {"source": "TraceRecorder", "mode": "smoke"},
                "output": {"ok": True, "boundary": "not real online collection"},
                "model": "none",
                "usage_count": 0,
                "latency_ms": 0,
            },
        )
        path = recorder.end("Smoke trace completed. This is integration verification, not real research.", status="completed")
        return {"run_id": run_id, "path": str(path) if path else "", "steps": self.trace_to_verity_steps(run_id)}

    def run_bounded_local_evidence_workflow(self) -> dict[str, Any]:
        """Run a real Evolva WorkflowEngine over versioned local evidence only.

        This proves the runtime-to-Verity handoff. It intentionally performs no
        network collection and never represents the fixture as competitor facts.
        """
        from evolva.agent.core import EvolvaAgent
        from evolva.workflow.engine import WorkflowEngine

        report_id = "workflow-local-001"
        fixture_path = "apps/api/verity_api/fixtures/bounded_local_evidence.json"
        agent = EvolvaAgent(self.config, assume_yes=True)
        trace_run_id = agent.tracer.start(
            "Run bounded local-evidence workflow for Verity integration validation.",
            meta={"runtime": "evolva-workflow", "is_real_workflow": True, "is_real_research": False},
        )
        spec = {
            "id": "verity_bounded_local_evidence",
            "nodes": [
                {"id": "load_bounded_evidence", "type": "tool", "tool": "read_file", "args": {"path": fixture_path}},
                {"id": "confirm_payload", "type": "tool", "tool": "normalize_answer", "args": {"answer": "{{load_bounded_evidence}}"}, "depends_on": ["load_bounded_evidence"]},
            ],
        }
        result = WorkflowEngine(agent).run(spec)
        trace_path = agent.tracer.end(
            "Bounded local-evidence workflow completed; no online research was performed.",
            status="completed" if result.ok else "failed",
        )
        if not result.ok:
            return {"ok": False, "workflow": result.to_dict(), "trace_run_id": trace_run_id, "trace_path": str(trace_path or "")}

        payload = json.loads(result.outputs["load_bounded_evidence"])
        evidence_items = [{**item, **score_evidence(item)} for item in payload["evidence_items"]]
        claims = payload["claims"]
        analysis_pack = build_analysis_pack(
            report_id=report_id,
            research_goal=payload["research_goal"],
            dimensions=payload["dimensions"],
            claims=claims,
            evidence_items=evidence_items,
        )
        qa_result = run_qa_gate(analysis_pack)
        now = time.strftime("%Y-%m-%dT%H:%M:%S+08:00", time.localtime())
        persist_bounded_workflow_result(
            report_id=report_id,
            title="Evolva WorkflowEngine 本地受控证据验证",
            research_goal=payload["research_goal"],
            competitors=payload["competitors"],
            evidence_items=evidence_items,
            claims=claims,
            analysis_pack=analysis_pack,
            qa_result=qa_result,
            updated_at=now,
        )
        steps = self.trace_to_verity_steps(trace_run_id, report_id=report_id)
        for step in steps:
            if step["stage"] == "工具调用":
                step["evidence_ids"] = [item["id"] for item in evidence_items]
                step["report_sections"] = ["evidence", "analysis_pack"]
        replace_trace_steps(report_id, steps, source_prefix=trace_run_id)
        return {
            "ok": True,
            "report_id": report_id,
            "workflow": result.to_dict(),
            "trace_run_id": trace_run_id,
            "trace_path": str(trace_path or ""),
            "evidence_count": len(evidence_items),
            "claim_count": len(claims),
            "analysis_pack": analysis_pack,
            "qa_gate": qa_result,
            "trace_steps": len(steps),
            "boundary": "Uses versioned local fixture evidence only; it is not online competitor research.",
        }


def _agent_from_event(kind: str, data: dict[str, Any]) -> str:
    if kind == "multi_agent_auto_route":
        return "Research Orchestrator"
    if kind == "task_route":
        return "TaskRouter"
    if kind in {"tool_call", "tool_error", "policy_decision"}:
        return str(data.get("tool") or "ToolRunner")
    if kind.startswith("loop"):
        return "LoopRunner"
    return "EvolvaAgent"


def _status_from_event(kind: str, data: dict[str, Any]) -> str:
    if kind == "tool_error":
        return "failed"
    if kind == "policy_decision" and data.get("allowed") is False:
        return "blocked"
    if data.get("ok") is False:
        return "failed"
    return str(data.get("status") or "done")


def _task_from_event(kind: str, data: dict[str, Any]) -> str:
    if "task" in data:
        return str(data["task"])
    if kind == "policy_decision":
        return f"Check tool policy for {data.get('tool', 'tool')}"
    if kind == "tool_call":
        return f"Call tool {data.get('tool', 'tool')}"
    if kind == "task_route":
        return str(data.get("reason") or "Route task to expert roles")
    return kind.replace("_", " ")


def _output_from_event(kind: str, data: dict[str, Any]) -> Any:
    if "output" in data:
        return data["output"]
    if "report" in data:
        return data["report"]
    if "result_data" in data:
        return data["result_data"]
    return data


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
