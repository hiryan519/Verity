from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


Layer = Literal["L3 决策层", "L2 策略层", "L1 执行层"]
ToolStatus = Literal["allowed", "disabled"]


@dataclass(frozen=True)
class ToolPermission:
    key: str
    name: str
    status: ToolStatus
    description: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class OutputContract:
    pack_type: str
    summary: str
    required_fields: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "pack_type": self.pack_type,
            "summary": self.summary,
            "required_fields": list(self.required_fields),
        }


@dataclass(frozen=True)
class GovernanceSummary:
    memory: str
    skill: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ExpertContract:
    id: str
    name: str
    layer: Layer
    responsibility: str
    responsibilities: tuple[str, ...]
    boundaries: tuple[str, ...]
    tool_permissions: tuple[ToolPermission, ...]
    output_contract: OutputContract
    supports_multi_instance: bool
    instance_strategy: str
    governance: GovernanceSummary

    def to_summary(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "layer": self.layer,
            "responsibility": self.responsibility,
            "tool_permissions": [tool.to_dict() for tool in self.tool_permissions],
            "output_pack_type": self.output_contract.pack_type,
            "supports_multi_instance": self.supports_multi_instance,
            "instance_strategy": self.instance_strategy,
        }

    def to_detail(self) -> dict:
        return {
            **self.to_summary(),
            "responsibilities": list(self.responsibilities),
            "boundaries": list(self.boundaries),
            "output_contract": self.output_contract.to_dict(),
            "governance": self.governance.to_dict(),
        }


NO_EXTERNAL_RESEARCH_TOOLS = (
    ToolPermission("public_web_search", "公开网页搜索", "disabled", "不直接检索公开网页，由证据采集专家或系统模块负责。"),
    ToolPermission("public_web_read", "公开网页读取", "disabled", "不直接读取网页正文，只处理被路由后的结构化输入。"),
    ToolPermission("user_url_read", "用户 URL 读取", "disabled", "不直接读取用户链接，由证据采集专家处理。"),
    ToolPermission("code_executor", "代码执行器", "disabled", "P0 不开放通用代码执行环境。"),
)


EXPERT_CONTRACTS: tuple[ExpertContract, ...] = (
    ExpertContract(
        id="research_orchestrator",
        name="研究编排专家",
        layer="L3 决策层",
        responsibility="将 Human Gate 确认后的研究目标转化为可执行、可审计的多 Agent 计划。",
        responsibilities=(
            "拆解研究范围、问题、专家任务、并行组和依赖关系。",
            "选择完成任务所需的最小专家集合，并说明未派出专家的原因。",
            "在 QA 首次返工时生成修订计划。",
        ),
        boundaries=(
            "不直接采集网页、生成 Evidence、Claim 或最终报告。",
            "不静默增加竞品、市场或分析维度。",
            "Candidate Memory 只能作为目标专家提示，不能扩大范围或成为事实依据。",
        ),
        tool_permissions=NO_EXTERNAL_RESEARCH_TOOLS,
        output_contract=OutputContract(
            pack_type="Research Plan",
            summary="研究范围、专家路由、并行依赖、数据缺口和计划版本。",
            required_fields=("scope_summary", "expert_routes", "parallel_groups", "data_gaps", "plan_version"),
        ),
        supports_multi_instance=False,
        instance_strategy="单次研究默认一个编排实例；QA 首次返工时可生成一次修订计划。",
        governance=GovernanceSummary(
            memory="Active Memory 可影响研究重点、专家选择与风险偏好；Candidate 只暴露目标专家和相关性提示。",
            skill="P0 不预置多个编排 Skill；调研范围、来源边界和返工上限属于系统机制。",
        ),
    ),
    ExpertContract(
        id="evidence_collector",
        name="证据采集专家",
        layer="L1 执行层",
        responsibility="将证据计划转化为可复查、可评分、可绑定 Claim 的 Evidence。",
        responsibilities=(
            "检索或读取公开网页、用户 URL 和用户附件。",
            "提取关键原文片段、来源元信息、内容哈希和风险提示。",
            "生成 Evidence Candidate 并进入规则评分。",
        ),
        boundaries=(
            "搜索结果只用于发现候选 URL，不能直接成为 Evidence。",
            "不登录、不绕过反爬、不处理验证码，不把付费墙或搜索摘要伪装成正文证据。",
            "读取失败写入 Source Attempt，不计入可用 Evidence。",
        ),
        tool_permissions=(
            ToolPermission("public_web_search", "公开网页搜索", "allowed", "公开网页检索，需保留 URL 与采集时间。"),
            ToolPermission("public_web_read", "公开网页读取", "allowed", "读取公开可访问页面，提取关键原文片段。"),
            ToolPermission("user_url_read", "用户 URL 读取", "allowed", "读取用户主动提供的公开链接。"),
            ToolPermission("user_attachment_read", "用户附件读取", "allowed", "读取用户主动提供的附件材料。"),
            ToolPermission("code_executor", "代码执行器", "disabled", "P0 不开放通用代码执行环境。"),
        ),
        output_contract=OutputContract(
            pack_type="Evidence Items",
            summary="可复查 Evidence、Source Attempt、content_hash、评分输入与风险。",
            required_fields=("evidence_id", "source_url", "captured_at", "key_excerpt", "content_hash", "risk_notes"),
        ),
        supports_multi_instance=True,
        instance_strategy="可按竞品、维度、来源类型并行启动多个采集实例，并由 Evidence Router 去重和路由。",
        governance=GovernanceSummary(
            memory="Active Memory 可影响来源偏好和采集失败模式；Candidate 只能低权重试用。",
            skill="来源规则、Evidence 结构和评分机制不是 Skill；可重复验证的采集方法才沉淀为 Skill。",
        ),
    ),
    ExpertContract(
        id="product_analyst",
        name="产品分析专家",
        layer="L2 策略层",
        responsibility="把产品相关 Evidence Slice 转化为产品维度的 Claim、对比项、风险和数据缺口。",
        responsibilities=(
            "分析产品定位、核心功能、用户流程、产品边界和差异化策略。",
            "区分官网宣传、可复查产品能力和推断。",
            "在证据不足时输出 data_gap 或补证建议。",
        ),
        boundaries=(
            "不直接采集网页证据，不读取全量 Evidence Store。",
            "不做价格结论，不分析竞品用户公开反馈体验好坏。",
            "Memory 只能影响分析方法，不能支撑事实结论。",
        ),
        tool_permissions=NO_EXTERNAL_RESEARCH_TOOLS,
        output_contract=OutputContract(
            pack_type="Product Analysis Pack",
            summary="产品维度 Claims、对比项、Claim-Evidence 绑定、冲突证据和 data_gap。",
            required_fields=("claims", "comparison_items", "evidence_ids", "risk_notes", "data_gaps"),
        ),
        supports_multi_instance=True,
        instance_strategy="可按竞品、产品维度或 Evidence Slice 分批并行，最终合并为总 Product Analysis Pack。",
        governance=GovernanceSummary(
            memory="Active Memory 可影响产品分析侧重点；Candidate 仅在目标对象匹配时低权重试用。",
            skill="P0 不预置产品分析 Skill；功能边界拆解等方法需经多次验证后沉淀。",
        ),
    ),
    ExpertContract(
        id="pricing_analyst",
        name="定价策略专家",
        layer="L2 策略层",
        responsibility="分析竞品如何通过价格、套餐、限制条件和价值包装影响用户决策。",
        responsibilities=(
            "分析定价结构、套餐边界、计费单位、免费策略和价格门槛。",
            "识别不可比项、隐藏限制、企业版不透明和价格归一化口径。",
            "输出定价维度 Claim、对比矩阵、风险和 data_gap。",
        ),
        boundaries=(
            "不直接采集网页证据，不判断产品功能本身强弱。",
            "不把官网标价推断为真实成交价格。",
            "不把不同计费单位粗暴比较为谁更便宜。",
        ),
        tool_permissions=NO_EXTERNAL_RESEARCH_TOOLS,
        output_contract=OutputContract(
            pack_type="Pricing Analysis Pack",
            summary="定价 Claims、套餐/计费单位矩阵、归一化说明、不可比项和风险。",
            required_fields=("pricing_claims", "pricing_matrix", "normalization_notes", "risk_notes", "data_gaps"),
        ),
        supports_multi_instance=True,
        instance_strategy="可按竞品、套餐类型或计费单位分批分析，最终合并为总 Pricing Analysis Pack。",
        governance=GovernanceSummary(
            memory="Active Memory 可影响价格归一化侧重点；Memory 不能作为价格事实证据。",
            skill="套餐边界拆解、单位价格归一等方法需经验证后沉淀为 Skill。",
        ),
    ),
    ExpertContract(
        id="user_experience_analyst",
        name="用户体验分析专家",
        layer="L2 策略层",
        responsibility="分析竞品终端用户在合法、可复查来源中表达的体验、痛点、价值感知和语义风险。",
        responsibilities=(
            "识别痛点、感知价值、反馈分歧、样本限制和语义风险。",
            "判断 evidence_coverage 为 sufficient、limited、insufficient_evidence 或 not_available。",
            "证据不足时诚实输出空体验结论和 data_gap。",
        ),
        boundaries=(
            "不做全网舆情监控，不绕过平台访问限制。",
            "不把情绪分类当最终事实，不用单条评论支撑强结论。",
            "不把官方客户案例等同于自然用户反馈。",
        ),
        tool_permissions=NO_EXTERNAL_RESEARCH_TOOLS,
        output_contract=OutputContract(
            pack_type="User Experience Analysis Pack",
            summary="体验 Claims、痛点、感知价值、分歧、语义风险、样本限制和 data_gap。",
            required_fields=("evidence_coverage", "experience_claims", "semantic_risks", "sample_limits", "data_gaps"),
        ),
        supports_multi_instance=True,
        instance_strategy="可按竞品、来源类型或体验主题分批分析；证据不足时允许输出空 Claim。",
        governance=GovernanceSummary(
            memory="Active Memory 可影响反讽风险、官方案例偏差和样本不足检查重点。",
            skill="反讽识别、样本限制评估等方法需经验证后沉淀为 Skill。",
        ),
    ),
    ExpertContract(
        id="cross_validator",
        name="交叉验证专家",
        layer="L2 策略层",
        responsibility="检查不同专家输出的 Claim、Evidence、风险和 data_gap 是否能够共同进入同一份报告。",
        responsibilities=(
            "发现 Claim 冲突、证据错配、过强结论和来源越界。",
            "合并跨专家 data_gap 和风险。",
            "提出 keep、downgrade、mark_conflict、needs_rework 或 report_with_risk 建议。",
        ),
        boundaries=(
            "不采集新证据，不生成新的业务事实或最终报告。",
            "不替代 QA Gate 做整体放行。",
            "不为了消除冲突而强行合并矛盾结论。",
        ),
        tool_permissions=NO_EXTERNAL_RESEARCH_TOOLS,
        output_contract=OutputContract(
            pack_type="Cross Validation Pack",
            summary="Claim 检查、冲突、证据误用、降级建议、合并 data_gap 和返工建议。",
            required_fields=("claim_checks", "conflicts", "evidence_misuse", "downgrade_suggestions", "merged_data_gaps"),
        ),
        supports_multi_instance=True,
        instance_strategy="可按内部一致性和跨专家组合拆成多个检查实例，再由汇总实例输出 Cross Validation Pack。",
        governance=GovernanceSummary(
            memory="Active Memory 可影响一致性检查重点；Memory 不能作为事实证据。",
            skill="Claim-Evidence 错配、跨维度冲突等检查方法需经验证后沉淀。",
        ),
    ),
    ExpertContract(
        id="qa_agent",
        name="QA 质检专家",
        layer="L2 策略层",
        responsibility="基于 QA Brief 判断 Analysis Pack 是否达到可以交给报告撰写专家的标准。",
        responsibilities=(
            "检查证据绑定、结论强度、来源边界、交叉验证处理、风险披露和范围对齐。",
            "决定 pass、rework、pass_with_risk 或 need_human_review。",
            "为问题选择 fix_in_pack、downgrade、keep_as_conflict、mark_data_gap 或 request_more_evidence 等处理路径。",
        ),
        boundaries=(
            "不采集新证据，不重新做产品、定价或用户体验分析。",
            "不读取全量子 Pack，只读取 QA Brief 和必要局部片段。",
            "不允许无限返工；最多触发 1 次返工。",
        ),
        tool_permissions=NO_EXTERNAL_RESEARCH_TOOLS,
        output_contract=OutputContract(
            pack_type="QA Gate Result",
            summary="QA 状态、评分、硬门槛失败、问题处理路径、目标专家和最终原因。",
            required_fields=("qa_status", "scores", "hard_failures", "issues", "issue_handling_paths", "rework_count"),
        ),
        supports_multi_instance=False,
        instance_strategy="默认一个 QA 实例读取 QA Brief；需要细查时按 Claim ID / Evidence ID 局部回查。",
        governance=GovernanceSummary(
            memory="Active Memory 可影响 QA 检查重点；QA 返工经验可进入 Memory Candidate。",
            skill="高价值 QA 检查规则需多次验证后沉淀为 Skill 草稿。",
        ),
    ),
    ExpertContract(
        id="report_writer",
        name="报告撰写专家",
        layer="L1 执行层",
        responsibility="把通过 QA Gate 的 Analysis Pack 写成可读、可追溯、能展示风险的报告。",
        responsibilities=(
            "组织执行摘要、产品、定价、用户体验、风险、引用和决策链路章节。",
            "保留 Claim 与 Evidence 的引用关系。",
            "通过总编实例统一口径、引用、风险和风格。",
        ),
        boundaries=(
            "不采集新证据，不新增 Analysis Pack 外的核心结论。",
            "不把 unsupported、conflicted、insufficient_evidence 或 not_available 写成确定结论。",
            "不生成没有数据表支撑的图表。",
        ),
        tool_permissions=(
            ToolPermission("report_renderer", "报告渲染器", "allowed", "将报告草稿渲染为 Markdown、HTML、PDF 或前端展示。"),
            ToolPermission("table_generator", "表格生成器", "allowed", "基于通过 QA 的结构化数据生成表格。"),
            ToolPermission("chart_spec_generator", "图表规范生成器", "allowed", "基于结构化数据生成可追溯图表规范。"),
            ToolPermission("citation_indexer", "引用索引生成器", "allowed", "生成 Claim 与 Evidence 的引用索引。"),
            ToolPermission("public_web_search", "公开网页搜索", "disabled", "不在写作阶段新增外部证据。"),
            ToolPermission("public_web_read", "公开网页读取", "disabled", "不在写作阶段读取网页正文。"),
            ToolPermission("user_url_read", "用户 URL 读取", "disabled", "不在写作阶段读取用户链接。"),
            ToolPermission("code_executor", "通用代码执行器", "disabled", "P0 不开放自由计算，只允许受控渲染工具。"),
        ),
        output_contract=OutputContract(
            pack_type="Traceable Report Draft",
            summary="报告章节、风险披露、引用索引、表格/图表规范和 Trace 摘要。",
            required_fields=("sections", "claim_evidence_refs", "risk_disclosures", "data_gaps", "trace_summary"),
        ),
        supports_multi_instance=True,
        instance_strategy="可拆成章节写作实例并行，必须经过总编实例合并后交给 Report Renderer。",
        governance=GovernanceSummary(
            memory="Active Memory 可影响表达偏好和引用展示格式；Memory 不能新增事实。",
            skill="报告结构优化、风险提示表达等方法需由用户反馈和 QA 结果验证后沉淀。",
        ),
    ),
)


EXPERT_REGISTRY_SOURCE = {
    "mode": "expert-registry",
    "seed": "mechanism-contracts",
    "is_real_workflow": False,
    "note": "Read-only expert governance contracts from docs/MECHANISM.md; not real online expert execution.",
}


def list_expert_contracts() -> list[dict]:
    return [contract.to_summary() for contract in EXPERT_CONTRACTS]


def get_expert_contract(expert_id: str) -> dict | None:
    for contract in EXPERT_CONTRACTS:
        if contract.id == expert_id:
            return contract.to_detail()
    return None
