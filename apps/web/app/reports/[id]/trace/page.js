import Link from "next/link";
import { Blocks, ChevronLeft, Clock3, Cpu, Database, Funnel, ListChecks, Wrench } from "lucide-react";
import { getApiData } from "@/lib/api";

export const dynamic = "force-dynamic";

const stageNames = {
  plan: "需求理解", orchestration: "编排派遣", collect: "证据采集", evidence: "证据采集",
  analysis: "交叉分析", cross_validation: "交叉分析", report: "报告撰写", report_writer: "报告撰写", qa: "质检审裁", delivery: "签发交付"
};

const fallbackSteps = [
  { id: "mock-89", stage: "需求理解", agent: "研究编排专家", task: "拆解调研计划", model: "默认模型", token_count: 1523, duration_ms: 35300, status: "completed", prompt: "基于用户确认的目标与范围，生成研究计划。", input: { scope: "AI 协作写作与知识工作台" }, output: { tasks: ["证据采集", "产品分析", "定价策略", "用户体验分析"] } },
  { id: "mock-90", stage: "编排派遣", agent: "研究编排专家", task: "指派最小专家集合", model: "默认模型", token_count: 4471, duration_ms: 24800, status: "completed", prompt: "根据研究计划选择必要专家，不无脑派出全部专家。", input: { dimensions: 4 }, output: { experts: ["证据采集专家", "产品分析专家", "定价策略专家", "用户体验分析专家"] } },
  { id: "mock-91", stage: "证据采集", agent: "证据采集专家", task: "采集公开网页与用户 URL 证据", model: "规则执行（非 LLM）", token_count: 0, duration_ms: 0, status: "completed", prompt: "", input: { source_scope: "公开网页 + 用户主动提供 URL" }, output: { evidence_count: 9, note: "示例数据" } },
  { id: "mock-105", stage: "报告撰写", agent: "报告撰写专家", task: "基于通过 QA 的 Analysis Pack 撰写章节", model: "默认模型", token_count: 6059, duration_ms: 38670, status: "completed", prompt: "只使用通过 QA 的结论；核心判断必须绑定 evidence_id；数据缺口不得改写为强结论。", input: { analysis_pack: "mock-analysis-pack", qa_status: "pass_with_risk" }, output: { key_takeaway: "套餐边界比价格数字更影响购买决策", risk: "用户体验样本不足" } },
  { id: "mock-106", stage: "质检审裁", agent: "QA 质检专家", task: "检查 Analysis Pack 的证据充分性与数据缺口风险", model: "默认模型", token_count: 2864, duration_ms: 19400, status: "completed", prompt: "", input: { rework_count: 0 }, output: { status: "pass_with_risk", gaps: 1 } }
];

function displayStage(stage = "") {
  const key = stage.toLowerCase().replaceAll(" ", "_");
  return stageNames[key] || stage || "未命名阶段";
}

function readable(value) {
  if (typeof value === "string") return value;
  return JSON.stringify(value ?? {}, null, 2);
}

export default async function TracePage({ params }) {
  const { id } = await params;
  const { item, dataSource, error } = await getApiData(`/api/reports/${id}`);
  const apiSteps = item?.trace_steps || [];
  const isFallback = !apiSteps.length && !item;
  const traceSteps = apiSteps.length ? apiSteps : isFallback ? fallbackSteps : [];
  const totalToken = traceSteps.reduce((sum, step) => sum + (step.token_count || 0), 0);
  const totalDuration = traceSteps.reduce((sum, step) => sum + (step.duration_ms || 0), 0);
  const expandedIndex = Math.max(0, traceSteps.findIndex((step) => displayStage(step.stage) === "报告撰写"));

  return (
    <section className="trace-audit">
      <header className="audit-header">
        <div className="audit-title">
          <Link href={`/reports/${id}`} className="audit-back" aria-label="返回报告"><ChevronLeft aria-hidden="true" /></Link>
          <div>
            <h2>Agent 决策日志 · Trace</h2>
            <p>回放每个 Agent 的阶段成果、运行上下文与脱敏输入输出。{isFallback ? "当前展示 Mock Trace。" : `数据源：${dataSource?.mode || "local-db"}。`}</p>
          </div>
        </div>
        <div className="audit-stats" aria-label="Trace 全局统计">
          <span><Cpu aria-hidden="true" />{totalToken.toLocaleString()} tokens</span>
          <span><Clock3 aria-hidden="true" />{(totalDuration / 1000).toFixed(1)}s</span>
          <span><ListChecks aria-hidden="true" />{traceSteps.length} 步</span>
        </div>
      </header>

      {error && !isFallback ? <p className="trace-error">API 未连接：{error}</p> : null}
      {!traceSteps.length && !error ? <div className="workflow-empty"><Blocks aria-hidden="true" /><strong>当前 Run 尚未产生 Trace</strong><p>研究可能尚未开始，或执行过程中没有写入可展示的 Trace。</p></div> : null}

      {traceSteps.length ? <div className="audit-filters" aria-label="Trace 阶段筛选">
        <span className="audit-filter-icon"><Funnel aria-hidden="true" /></span>
        {['全部', '需求理解', '编排派遣', '证据采集', '交叉分析', '报告撰写', '质检审裁', '签发交付'].map((filter, index) => (
          <button key={filter} className={`audit-filter ${index === 0 ? "active" : ""}`}>{filter}</button>
        ))}
      </div> : null}

      {traceSteps.length ? <div className="audit-timeline">
        {traceSteps.map((step, index) => {
          const stage = displayStage(step.stage);
          const expanded = index === expandedIndex;
          return (
            <article key={step.id || index} className="audit-step">
              <span className="audit-marker">{String(index + 1).padStart(2, "0")}</span>
              <div className="audit-card">
                <div className="audit-card-main">
                  <div className="audit-card-left">
                    <span className="audit-avatar">{step.agent?.includes("QA") ? "QA" : step.agent?.slice(0, 1) || "A"}</span>
                    <div>
                      <div className="audit-meta-row"><span className="audit-phase">{stage}</span><span>{step.agent}</span><span>{step.status}</span></div>
                      <h3 className="audit-action">{step.task}</h3>
                    </div>
                  </div>
                  <div className="audit-card-right">
                    <span className="audit-model">{step.model || "未记录模型"}</span>
                    <span className="audit-cost">{step.token_count || 0} tok · {((step.duration_ms || 0) / 1000).toFixed(1)}s</span>
                  </div>
                </div>

                {expanded ? (
                  <div className="audit-expanded">
                    <div className="audit-context-grid" aria-label="本次运行上下文">
                      <article className="audit-context-card"><strong><Cpu aria-hidden="true" />Model</strong><p><code>{step.model || "未记录"}</code><br />本次 Trace 实际记录模型</p></article>
                      <article className="audit-context-card"><strong><Wrench aria-hidden="true" />Tools Used</strong><p>{step.tools_used?.join?.("、") || "未记录外部工具调用"}</p></article>
                      <article className="audit-context-card"><strong><Database aria-hidden="true" />Memory Used</strong><p><code>{step.memory_used?.length || 0}</code> 条运行记忆</p></article>
                      <article className="audit-context-card"><strong><Blocks aria-hidden="true" />Skill Used</strong><p>{step.skills_used?.join?.("、") || "未记录 Skill"}</p></article>
                    </div>
                    <div className="audit-log"><strong>Prompt / Input（脱敏）</strong><pre>{readable(step.prompt)}{step.prompt ? "\n\n" : ""}{readable(step.input)}</pre></div>
                    <div className="audit-log"><strong>Output（阶段成果）</strong><pre>{readable(step.output)}</pre></div>
                    <div className="audit-expanded-foot"><span>{step.token_count || 0} tokens</span><span>{((step.duration_ms || 0) / 1000).toFixed(2)}s</span><span>Evidence: {step.evidence_ids?.length || 0}</span><span>Sections: {step.report_sections?.length || 0}</span></div>
                  </div>
                ) : null}
              </div>
            </article>
          );
        })}
      </div> : null}
    </section>
  );
}
