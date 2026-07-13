from __future__ import annotations

from dataclasses import dataclass

from .expert_registry import EXPERT_CONTRACTS


@dataclass(frozen=True)
class SchemaField:
    name: str
    field_type: str
    description: str
    required: bool = True

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.field_type,
            "description": self.description,
            "required": self.required,
        }


@dataclass(frozen=True)
class ExpertExecutionContract:
    expert_id: str
    input_schema: tuple[SchemaField, ...]
    output_schema: tuple[SchemaField, ...]
    prompt_fragment: str
    prompt_visibility: str = "internal_contract"
    is_page_editable: bool = False
    is_real_llm_execution: bool = False

    def to_summary(self) -> dict:
        return {
            "expert_id": self.expert_id,
            "prompt_visibility": self.prompt_visibility,
            "is_page_editable": self.is_page_editable,
            "is_real_llm_execution": self.is_real_llm_execution,
            "input_field_count": len(self.input_schema),
            "output_field_count": len(self.output_schema),
        }

    def to_detail(self) -> dict:
        return {
            **self.to_summary(),
            "input_schema": [field.to_dict() for field in self.input_schema],
            "output_schema": [field.to_dict() for field in self.output_schema],
            "prompt_fragment": self.prompt_fragment,
        }


COMMON_INPUT_FIELDS = (
    SchemaField("run_id", "string", "Workflow run identifier."),
    SchemaField("research_goal", "string", "Human-confirmed research goal."),
    SchemaField("scope", "object", "Human Gate confirmed competitors, dimensions, market, audience, and time range."),
    SchemaField("active_memory", "array", "Scoped active memory items allowed to influence method, not facts.", required=False),
    SchemaField("candidate_memory_hints", "array", "Targeted candidate memory hints for low-weight trial only.", required=False),
)


EVIDENCE_SLICE_INPUT = (
    SchemaField("evidence_slice", "array", "Routed Evidence Slice with Evidence IDs, excerpts, scores, risks, and content_hash."),
    SchemaField("slice_budget", "object", "Token budget, batch id, and coverage metadata for this slice."),
)


CLAIM_OUTPUT_FIELDS = (
    SchemaField("claims", "array", "Structured claims with claim_id, claim_text, claim_status, evidence_ids, reasoning, and risks."),
    SchemaField("data_gaps", "array", "Evidence gaps that prevent stronger conclusions."),
    SchemaField("risk_notes", "array", "Risks that must be inherited by downstream validation, QA, or report writing."),
)


def _prompt(role: str, task: str, hard_rules: tuple[str, ...]) -> str:
    lines = [
        f"你是 Verity 的{role}。",
        task,
        "只使用输入中允许的结构化材料，不得自行扩大 Human Gate 范围。",
        "Memory 只能影响方法和关注点，不能作为事实证据。",
        "如果证据不足，输出 data_gap / insufficient_evidence，而不是补故事。",
        "输出必须符合本专家的结构化 schema，并保留 Claim 与 Evidence ID 的绑定。",
        *hard_rules,
    ]
    return "\n".join(lines)


EXPERT_EXECUTION_CONTRACTS: tuple[ExpertExecutionContract, ...] = (
    ExpertExecutionContract(
        expert_id="research_orchestrator",
        input_schema=(
            *COMMON_INPUT_FIELDS,
            SchemaField("user_provided_sources", "array", "User-provided URLs or attachments allowed by Human Gate.", required=False),
            SchemaField("expert_registry", "array", "Read-only expert registry entries."),
            SchemaField("qa_rework_issue", "object", "QA issue for the single allowed rework plan.", required=False),
        ),
        output_schema=(
            SchemaField("scope_summary", "object", "Confirmed scope summary."),
            SchemaField("expert_routes", "array", "Selected and skipped experts with reasons."),
            SchemaField("parallel_groups", "array", "Read-only parallel groups and sequential dependencies."),
            SchemaField("data_gaps", "array", "Known gaps before execution."),
            SchemaField("plan_version", "string", "Initial or rework plan version."),
        ),
        prompt_fragment=_prompt(
            "研究编排专家",
            "将用户确认后的研究目标转化为可执行、可审计的多 Agent 计划。",
            (
                "不要直接生成 Evidence、Claim 或报告。",
                "选择完成任务所需的最小专家集合，不为展示多 Agent 而全员派出。",
            ),
        ),
    ),
    ExpertExecutionContract(
        expert_id="evidence_collector",
        input_schema=(
            *COMMON_INPUT_FIELDS,
            SchemaField("evidence_plan", "object", "Source plan from the orchestrator."),
            SchemaField("allowed_sources", "array", "Public web and user-provided sources only."),
        ),
        output_schema=(
            SchemaField("evidence_items", "array", "Readable Evidence with source metadata, key excerpt, score inputs, risks, and content_hash."),
            SchemaField("source_attempts", "array", "Failed reads or blocked sources that cannot support claims."),
            SchemaField("collection_trace", "array", "Queries, URLs, read status, and extraction notes."),
        ),
        prompt_fragment=_prompt(
            "证据采集专家",
            "将证据计划转化为可复查、可评分、可绑定 Claim 的 Evidence。",
            (
                "搜索摘要不能直接作为 Evidence。",
                "不登录、不绕过反爬、不处理验证码。",
                "每条成功读取的 Evidence 必须保留 content_hash。",
            ),
        ),
    ),
    ExpertExecutionContract(
        expert_id="product_analyst",
        input_schema=(*COMMON_INPUT_FIELDS, *EVIDENCE_SLICE_INPUT),
        output_schema=(
            *CLAIM_OUTPUT_FIELDS,
            SchemaField("comparison_items", "array", "Product positioning, feature, user-flow, and boundary comparison items."),
        ),
        prompt_fragment=_prompt(
            "产品分析专家",
            "把产品相关 Evidence Slice 转化为产品维度的 Claim、对比项、风险和数据缺口。",
            (
                "不要直接采集网页，不读取全量 Evidence Store。",
                "不要做价格结论或用户体验好坏判断。",
                "区分官网宣传、可复查产品能力和推断。",
            ),
        ),
    ),
    ExpertExecutionContract(
        expert_id="pricing_analyst",
        input_schema=(*COMMON_INPUT_FIELDS, *EVIDENCE_SLICE_INPUT),
        output_schema=(
            *CLAIM_OUTPUT_FIELDS,
            SchemaField("pricing_matrix", "array", "Plans, price, billing unit, limits, and Evidence IDs."),
            SchemaField("normalization_notes", "array", "Comparable-unit notes or explicit incomparability explanations."),
        ),
        prompt_fragment=_prompt(
            "定价策略专家",
            "分析竞品如何通过价格、套餐、限制条件和价值包装影响用户决策。",
            (
                "不要把官网标价推断为真实成交价格。",
                "不同计费单位必须归一化或明确不可比。",
                "企业版、折扣和区域价格不透明时必须标注风险。",
            ),
        ),
    ),
    ExpertExecutionContract(
        expert_id="user_experience_analyst",
        input_schema=(*COMMON_INPUT_FIELDS, *EVIDENCE_SLICE_INPUT),
        output_schema=(
            SchemaField("evidence_coverage", "string", "sufficient, limited, insufficient_evidence, or not_available."),
            SchemaField("experience_claims", "array", "Experience claims; must be empty when evidence is insufficient or unavailable."),
            SchemaField("semantic_risks", "array", "Sarcasm, joking, missing context, translation, and platform risks."),
            SchemaField("sample_limits", "array", "Sample size and source limitations."),
            SchemaField("data_gaps", "array", "Missing user-experience evidence."),
        ),
        prompt_fragment=_prompt(
            "用户体验分析专家",
            "分析竞品终端用户在合法、可复查来源中表达的体验、痛点、价值感知和语义风险。",
            (
                "不要做全网舆情监控。",
                "事实完整性优先于内容丰满度；证据不足时输出 insufficient_evidence 或 not_available。",
                "不要把情绪分类当事实，不用单条评论支撑强结论。",
            ),
        ),
    ),
    ExpertExecutionContract(
        expert_id="cross_validator",
        input_schema=(
            *COMMON_INPUT_FIELDS,
            SchemaField("analysis_packs", "array", "Product, pricing, UX, and other expert pack fragments."),
            SchemaField("claim_evidence_index", "array", "Claim to Evidence mappings."),
        ),
        output_schema=(
            SchemaField("claim_checks", "array", "Per-claim keep, downgrade, conflict, or rework checks."),
            SchemaField("conflicts", "array", "Cross-expert or internal conflicts."),
            SchemaField("evidence_misuse", "array", "Claims using unsuitable Evidence."),
            SchemaField("downgrade_suggestions", "array", "Suggested status or strength downgrades."),
            SchemaField("merged_data_gaps", "array", "Deduplicated and cross-linked gaps."),
        ),
        prompt_fragment=_prompt(
            "交叉验证专家",
            "检查不同专家输出的 Claim、Evidence、风险和 data_gap 是否能够共同进入同一份报告。",
            (
                "不要采集新证据，不生成新业务事实。",
                "不要替代 QA Gate 做整体放行。",
                "真实冲突应保留为风险或分歧，不要强行合并。",
            ),
        ),
    ),
    ExpertExecutionContract(
        expert_id="qa_agent",
        input_schema=(
            *COMMON_INPUT_FIELDS,
            SchemaField("qa_brief", "object", "Rule-built QA Brief with issue index and risk summary."),
            SchemaField("cross_validation_pack", "object", "Cross Validation Pack."),
            SchemaField("rework_count", "integer", "Current rework count."),
        ),
        output_schema=(
            SchemaField("qa_status", "string", "pass, rework, pass_with_risk, or need_human_review."),
            SchemaField("scores", "object", "Weighted QA dimension scores."),
            SchemaField("hard_failures", "array", "Hard gate failures."),
            SchemaField("issues", "array", "QA issues."),
            SchemaField("issue_handling_paths", "array", "fix_in_pack, downgrade, mark_data_gap, request_more_evidence, and related paths."),
            SchemaField("rework_count", "integer", "Current rework count, max 1."),
        ),
        prompt_fragment=_prompt(
            "QA 质检专家",
            "基于 QA Brief 判断 Analysis Pack 是否达到可以交给报告撰写专家的标准。",
            (
                "不要读取全量子 Pack；必要时按 ID 局部回查。",
                "不要亲自解决问题，只决定处理路径。",
                "最多触发 1 次返工。",
            ),
        ),
    ),
    ExpertExecutionContract(
        expert_id="report_writer",
        input_schema=(
            *COMMON_INPUT_FIELDS,
            SchemaField("analysis_pack", "object", "QA-passed or pass_with_risk Analysis Pack."),
            SchemaField("qa_gate_result", "object", "QA decision and risk requirements."),
            SchemaField("claim_evidence_index", "array", "Claim and Evidence references."),
            SchemaField("report_outline", "object", "Report outline and section constraints."),
        ),
        output_schema=(
            SchemaField("sections", "array", "Report sections."),
            SchemaField("claim_evidence_refs", "array", "Section to Claim/Evidence mappings."),
            SchemaField("risk_disclosures", "array", "Risks that must be visible in report."),
            SchemaField("table_specs", "array", "Table specifications backed by structured data.", required=False),
            SchemaField("chart_specs", "array", "Chart specifications backed by data tables.", required=False),
            SchemaField("trace_summary", "object", "User-facing decision trace summary."),
        ),
        prompt_fragment=_prompt(
            "报告撰写专家",
            "把通过 QA Gate 的 Analysis Pack 写成可读、可追溯、能展示风险的报告。",
            (
                "不要新增 Analysis Pack 外的核心结论。",
                "不要隐藏 data_gap、QA 风险、不可比项或样本限制。",
                "图表和表格必须来自通过 QA 的结构化数据。",
            ),
        ),
    ),
)


EXECUTION_CONTRACT_SOURCE = {
    "mode": "expert-execution-contracts",
    "seed": "mechanism-contracts",
    "is_real_workflow": False,
    "note": "Prompt/schema contracts for future LLM-backed expert execution; not live LLM execution.",
}


def list_execution_contracts() -> list[dict]:
    return [contract.to_summary() for contract in EXPERT_EXECUTION_CONTRACTS]


def get_execution_contract(expert_id: str) -> dict | None:
    for contract in EXPERT_EXECUTION_CONTRACTS:
        if contract.expert_id == expert_id:
            return contract.to_detail()
    return None


def validate_execution_contract_coverage() -> bool:
    registered_experts = {contract.id for contract in EXPERT_CONTRACTS}
    execution_experts = {contract.expert_id for contract in EXPERT_EXECUTION_CONTRACTS}
    return registered_experts == execution_experts
