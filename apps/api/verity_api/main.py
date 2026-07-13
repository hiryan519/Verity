from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .analysis import build_analysis_pack
from .db import (
    DATA_SOURCE,
    get_qa_result,
    create_memory_candidate,
    cite_knowledge_as_evidence,
    get_report,
    init_db,
    list_knowledge_items,
    list_memories,
    list_claims,
    list_evidence,
    list_reports,
    list_trace_steps,
    replace_trace_steps,
    record_memory_signal,
    update_memory_status,
)
from .evolva_adapter import EvolvaAdapter
from .expert_context import build_expert_context_from_db
from .expert_registry import EXPERT_REGISTRY_SOURCE, get_expert_contract, list_expert_contracts
from .expert_execution_contracts import (
    EXECUTION_CONTRACT_SOURCE,
    get_execution_contract,
    list_execution_contracts,
)
from .llm_execution import get_llm_provider_status, prepare_llm_expert_execution
from .mock_data import MOCK_NAVIGATION
from .qa import run_qa_gate
from .system_module_registry import (
    SYSTEM_MODULE_REGISTRY_SOURCE,
    get_system_module_contract,
    list_system_module_contracts,
)
from .verity_experts import VerityExpertRunner


class MemoryCandidateRequest(BaseModel):
    memory_type: str = Field(default="expert_lesson")
    content: str
    target_agent: str
    influence_target: str = Field(default="agent_checklist")
    effect_strategy: str | None = None
    source_type: str = Field(default="user_feedback")
    source_report_id: str | None = None
    source_ref: str = ""
    evidence: list[str] = Field(default_factory=list)
    confidence: int = 70
    risk_note: str = ""
    status: str = "candidate"


class FeedbackLessonRequest(BaseModel):
    report_id: str
    target_agent: str
    feedback: str
    source_ref: str = ""


class KnowledgeCitationRequest(BaseModel):
    report_id: str
    knowledge_id: str


class MemorySignalRequest(BaseModel):
    signal: str


class LLMExpertExecutionRequest(BaseModel):
    input_payload: dict = Field(default_factory=dict)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Verity Adapter API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    init_db()
    return {"status": "ok", "service": "verity-api", "data_source": DATA_SOURCE}


@app.get("/api/navigation")
def navigation() -> dict:
    return {"data_source": DATA_SOURCE, "items": MOCK_NAVIGATION}


@app.get("/api/reports")
def reports() -> dict:
    return {"data_source": DATA_SOURCE, "items": list_reports()}


@app.get("/api/reports/{report_id}")
def report_detail(report_id: str) -> dict:
    report = get_report(report_id)
    if report is None:
        return {"data_source": DATA_SOURCE, "item": None}

    return {
        "data_source": DATA_SOURCE,
        "item": {
            **report,
            "claims": list_claims(report_id),
            "evidence": list_evidence(report_id),
            "qa_gate": get_qa_result(report_id),
            "trace_steps": list_trace_steps(report_id),
        },
    }


@app.get("/api/reports/{report_id}/analysis-pack")
def analysis_pack(report_id: str) -> dict:
    report = get_report(report_id)
    if report is None:
        return {"data_source": DATA_SOURCE, "item": None}

    dimensions = ["产品定位", "核心场景", "定价策略", "用户声音", "证据缺口"]
    pack = build_analysis_pack(
        report_id=report_id,
        research_goal=report["summary"],
        dimensions=dimensions,
        claims=list_claims(report_id),
        evidence_items=list_evidence(report_id),
    )

    return {
        "data_source": DATA_SOURCE,
        "item": {
            "analysis_pack": pack,
            "qa_preview": run_qa_gate(pack),
        },
    }


@app.get("/api/experts")
def experts() -> dict:
    return {"data_source": EXPERT_REGISTRY_SOURCE, "items": list_expert_contracts()}


@app.get("/api/experts/{expert_id}")
def expert_detail(expert_id: str) -> dict:
    return {"data_source": EXPERT_REGISTRY_SOURCE, "item": get_expert_contract(expert_id)}


@app.get("/api/system-modules")
def system_modules() -> dict:
    return {"data_source": SYSTEM_MODULE_REGISTRY_SOURCE, "items": list_system_module_contracts()}


@app.get("/api/system-modules/{module_id}")
def system_module_detail(module_id: str) -> dict:
    return {"data_source": SYSTEM_MODULE_REGISTRY_SOURCE, "item": get_system_module_contract(module_id)}


@app.get("/api/expert-execution-contracts")
def expert_execution_contracts() -> dict:
    return {"data_source": EXECUTION_CONTRACT_SOURCE, "items": list_execution_contracts()}


@app.get("/api/expert-execution-contracts/{expert_id}")
def expert_execution_contract_detail(expert_id: str) -> dict:
    return {"data_source": EXECUTION_CONTRACT_SOURCE, "item": get_execution_contract(expert_id)}


@app.get("/api/llm/status")
def llm_status() -> dict:
    return {
        "data_source": {"mode": "llm-provider-status", "is_real_workflow": False},
        "item": get_llm_provider_status(),
    }


@app.post("/api/llm/experts/{expert_id}/prepare")
def llm_expert_prepare(expert_id: str, payload: LLMExpertExecutionRequest) -> dict:
    return {
        "data_source": {"mode": "llm-execution-boundary", "is_real_workflow": False},
        "item": prepare_llm_expert_execution(expert_id, payload.input_payload),
    }


@app.get("/api/experts/{expert_id}/runtime-context")
def expert_runtime_context(expert_id: str) -> dict:
    return {"data_source": DATA_SOURCE, "item": build_expert_context_from_db(expert_id)}


@app.get("/api/evidence")
def evidence(report_id: str | None = None) -> dict:
    return {"data_source": DATA_SOURCE, "items": list_evidence(report_id)}


@app.get("/api/knowledge")
def knowledge() -> dict:
    return {"data_source": DATA_SOURCE, "items": list_knowledge_items()}


@app.post("/api/knowledge/cite-as-evidence")
def knowledge_cite_as_evidence(payload: KnowledgeCitationRequest) -> dict:
    evidence_item = cite_knowledge_as_evidence(payload.report_id, payload.knowledge_id)
    if evidence_item is None:
        return {"data_source": DATA_SOURCE, "item": None}
    candidate = create_memory_candidate(
        memory_type="expert_lesson",
        content="来自用户知识库的内容已被引用为证据；若后续被用户认可，可抽象为专家 checklist 或报告风格经验。",
        target_agent="business_pricing_analyst",
        influence_target="agent_checklist",
        source_type="knowledge_highlight",
        source_report_id=payload.report_id,
        source_ref=payload.knowledge_id,
        evidence=[evidence_item["id"]],
        confidence=70,
        risk_note="知识库引用只能作为 candidate trial，不能自动 active。",
        status="candidate",
    )
    return {"data_source": DATA_SOURCE, "item": {"evidence": evidence_item, "memory_candidate": candidate}}


@app.get("/api/evolva/status")
def evolva_status() -> dict:
    adapter = EvolvaAdapter()
    return {"data_source": {"mode": "evolva-adapter", "is_real_workflow": False}, "item": adapter.status()}


@app.get("/api/evolva/traces")
def evolva_traces(limit: int = 20) -> dict:
    adapter = EvolvaAdapter()
    return {"data_source": {"mode": "evolva-adapter", "is_real_workflow": False}, "items": adapter.list_traces(limit=limit)}


@app.get("/api/evolva/traces/{run_id}/verity-steps")
def evolva_trace_steps(run_id: str, report_id: str = "mock-001") -> dict:
    adapter = EvolvaAdapter()
    return {
        "data_source": {"mode": "evolva-adapter", "is_real_workflow": False},
        "items": adapter.trace_to_verity_steps(run_id, report_id=report_id),
    }


@app.post("/api/evolva/smoke-trace")
def evolva_smoke_trace(report_id: str = "mock-001") -> dict:
    adapter = EvolvaAdapter()
    result = adapter.create_smoke_trace()
    steps = [{**step, "report_id": report_id} for step in result["steps"]]
    imported = replace_trace_steps(report_id, steps, source_prefix=result["run_id"])
    return {
        "data_source": {"mode": "evolva-adapter", "is_real_workflow": False},
        "item": {**result, "imported_trace_steps": imported, "report_id": report_id},
    }


@app.post("/api/evolva/workflows/bounded-local-evidence")
def evolva_bounded_local_evidence_workflow() -> dict:
    result = EvolvaAdapter().run_bounded_local_evidence_workflow()
    return {
        "data_source": {
            "mode": "evolva-workflow",
            "is_real_workflow": True,
            "is_real_research": False,
            "note": "Runs Evolva WorkflowEngine over versioned local fixture evidence; it does not collect online competitor data.",
        },
        "item": result,
    }


@app.get("/api/verity/experts")
def verity_experts() -> dict:
    runner = VerityExpertRunner()
    return {"data_source": {"mode": "verity-adapter", "is_real_workflow": False}, "items": runner.list_experts()}


@app.post("/api/verity/experts/run-minimal")
def verity_experts_run_minimal(report_id: str = "mock-001") -> dict:
    report = get_report(report_id)
    if report is None:
        return {"data_source": {"mode": "verity-adapter", "is_real_workflow": False}, "item": None}

    runner = VerityExpertRunner()
    result = runner.run_minimal_research(
        report_id=report_id,
        research_goal=report["summary"],
        claims=list_claims(report_id),
        evidence_items=list_evidence(report_id),
        dimensions=["产品定位", "核心场景", "定价策略", "用户声音", "证据缺口"],
    )
    return {"data_source": {"mode": "verity-adapter", "is_real_workflow": False}, "item": result}


@app.get("/api/memories")
def memories(status: str | None = None, target_agent: str | None = None) -> dict:
    return {"data_source": DATA_SOURCE, "items": list_memories(status=status, target_agent=target_agent)}


@app.post("/api/memories/candidates")
def memory_candidate(payload: MemoryCandidateRequest) -> dict:
    item = create_memory_candidate(
        memory_type=payload.memory_type,
        content=payload.content,
        target_agent=payload.target_agent,
        influence_target=payload.effect_strategy or payload.influence_target,
        source_type=payload.source_type,
        source_report_id=payload.source_report_id,
        source_ref=payload.source_ref,
        evidence=payload.evidence,
        confidence=payload.confidence,
        risk_note=payload.risk_note,
        status=payload.status,
    )
    return {"data_source": DATA_SOURCE, "item": item}


@app.post("/api/memories/from-feedback")
def memory_from_feedback(payload: FeedbackLessonRequest) -> dict:
    content = _feedback_to_lesson(payload.feedback, payload.target_agent)
    item = create_memory_candidate(
        memory_type="expert_lesson",
        content=content,
        target_agent=payload.target_agent,
        influence_target="agent_checklist",
        source_type="user_annotation",
        source_report_id=payload.report_id,
        source_ref=payload.source_ref,
        evidence=[payload.feedback],
        confidence=76,
        risk_note="用户反馈生成的专家经验，需要确认后影响后续执行。",
        status="candidate",
    )
    return {"data_source": DATA_SOURCE, "item": item}


@app.post("/api/memories/{memory_id}/activate")
def memory_activate(memory_id: str) -> dict:
    return {"data_source": DATA_SOURCE, "item": update_memory_status(memory_id, "active")}


@app.post("/api/memories/{memory_id}/quarantine")
def memory_quarantine(memory_id: str) -> dict:
    return {"data_source": DATA_SOURCE, "item": update_memory_status(memory_id, "quarantined")}


@app.post("/api/memories/{memory_id}/archive")
def memory_archive(memory_id: str) -> dict:
    return {"data_source": DATA_SOURCE, "item": update_memory_status(memory_id, "archived")}


@app.post("/api/memories/{memory_id}/signal")
def memory_signal(memory_id: str, payload: MemorySignalRequest) -> dict:
    return {"data_source": DATA_SOURCE, "item": record_memory_signal(memory_id, payload.signal)}


def _feedback_to_lesson(feedback: str, target_agent: str) -> str:
    text = feedback.strip()
    if target_agent == "business_pricing_analyst" and any(marker in text.lower() for marker in ["token", "api", "调用", "价格"]):
        return "价格分析不能只比较订阅价格或 API 标价，还必须比较同预算下的 token 可用量、调用次数、上下文长度、速率限制、免费额度和套餐限制。"
    return f"后续执行时需要检查用户指出的分析缺口：{text}"
