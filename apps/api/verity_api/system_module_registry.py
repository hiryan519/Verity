from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


ModuleVisibility = Literal["internal", "governance_view"]


@dataclass(frozen=True)
class ModuleIOContract:
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]

    def to_dict(self) -> dict:
        return {"inputs": list(self.inputs), "outputs": list(self.outputs)}


@dataclass(frozen=True)
class SystemModuleContract:
    id: str
    name: str
    category: str
    responsibility: str
    is_expert: bool
    uses_llm: bool
    visibility: ModuleVisibility
    io_contract: ModuleIOContract
    boundaries: tuple[str, ...]
    trace_requirements: tuple[str, ...]

    def to_summary(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "responsibility": self.responsibility,
            "is_expert": self.is_expert,
            "uses_llm": self.uses_llm,
            "visibility": self.visibility,
        }

    def to_detail(self) -> dict:
        return {
            **self.to_summary(),
            "io_contract": self.io_contract.to_dict(),
            "boundaries": list(self.boundaries),
            "trace_requirements": list(self.trace_requirements),
        }


SYSTEM_MODULE_CONTRACTS: tuple[SystemModuleContract, ...] = (
    SystemModuleContract(
        id="evidence_router",
        name="Evidence Router / Evidence Slice",
        category="evidence_control",
        responsibility="将多名证据采集专家产生的 Evidence 转成各分析专家可处理、可追溯的 Evidence Slice。",
        is_expert=False,
        uses_llm=False,
        visibility="governance_view",
        io_contract=ModuleIOContract(
            inputs=("Evidence Candidate", "Evidence score", "content_hash", "expert task", "token budget"),
            outputs=("Evidence Slice", "dedupe decisions", "routing tags", "slice budget metadata"),
        ),
        boundaries=(
            "不产生业务结论。",
            "不把证据压缩成不可追溯摘要。",
            "标签只用于路由，不作为事实结论。",
            "同一内容重复出现不自动提高可信度。",
        ),
        trace_requirements=(
            "记录覆盖 Evidence 数量、去重结果和 content_hash。",
            "记录每个 Evidence Slice 的目标专家、主题和 token 估算。",
            "记录被降权、合并或延后处理的证据原因。",
        ),
    ),
    SystemModuleContract(
        id="qa_brief_builder",
        name="QA Brief Builder",
        category="quality_control",
        responsibility="从结构化 Analysis Pack、Cross Validation Pack 和 Evidence Metadata 中抽取 QA 可审查的问题索引。",
        is_expert=False,
        uses_llm=False,
        visibility="governance_view",
        io_contract=ModuleIOContract(
            inputs=("Analysis Pack", "Cross Validation Pack", "Evidence Metadata", "Human Gate scope", "rework_count"),
            outputs=("QA Brief", "risk summary", "issue index", "local evidence snippets"),
        ),
        boundaries=(
            "不是 LLM 总结器。",
            "不读取全量自然语言材料做摘要。",
            "不决定 pass / rework，只为 QA 质检专家准备结构化风险输入。",
            "正常低风险 Claim 只保留统计，不展开全文。",
        ),
        trace_requirements=(
            "记录命中的 QA 规则和风险排序。",
            "记录进入 QA Brief 的 issue、Claim ID 和 Evidence ID。",
            "记录附带局部证据片段的原因。",
        ),
    ),
    SystemModuleContract(
        id="report_renderer",
        name="Report Renderer / Report Artifact Builder",
        category="report_artifact",
        responsibility="将 Traceable Report Draft、表格规范、图表规范和引用索引渲染为最终报告产物。",
        is_expert=False,
        uses_llm=False,
        visibility="governance_view",
        io_contract=ModuleIOContract(
            inputs=("Traceable Report Draft", "table specs", "chart specs", "citation index", "render target"),
            outputs=("Markdown report", "HTML report", "PDF-ready artifact", "frontend report payload"),
        ),
        boundaries=(
            "不新增 Analysis Pack 外的核心结论。",
            "不做自由计算或重新分析。",
            "不生成没有数据表支撑的图表。",
            "图表和表格必须保留数据来源或 Evidence ID。",
        ),
        trace_requirements=(
            "记录使用的渲染目标和模板版本。",
            "记录生成的表格、图表和引用索引。",
            "记录报告章节与 Claim / Evidence 的映射关系。",
        ),
    ),
)


SYSTEM_MODULE_REGISTRY_SOURCE = {
    "mode": "system-module-registry",
    "seed": "mechanism-contracts",
    "is_real_workflow": False,
    "note": "Read-only system module contracts from docs/MECHANISM.md; modules are not expert agents.",
}


def list_system_module_contracts() -> list[dict]:
    return [contract.to_summary() for contract in SYSTEM_MODULE_CONTRACTS]


def get_system_module_contract(module_id: str) -> dict | None:
    for contract in SYSTEM_MODULE_CONTRACTS:
        if contract.id == module_id:
            return contract.to_detail()
    return None
