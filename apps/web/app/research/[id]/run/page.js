import Link from "next/link";
import { ArrowRight, ExternalLink } from "lucide-react";
import { mockAgentActions, mockEvidence, mockPipeline } from "@/lib/mock-data";

const expertTeam = [["编", "研究编排专家"], ["证", "证据采集专家"], ["产", "产品分析专家"], ["价", "定价策略专家"], ["体", "用户体验分析专家"], ["验", "交叉验证专家"], ["QA", "QA 质检专家"]];

function actionShortName(agent) {
  if (agent.includes("Orchestrator")) return "编";
  if (agent.includes("Evidence")) return "证";
  return "价";
}

export default async function ResearchRunPage({ params }) {
  const { id } = await params;

  return (
    <section className="workflow-page route-section">
      <div className="section-head">
        <div>
          <p className="eyebrow">Agent Workflow</p>
          <h2>调研执行页</h2>
          <p>左侧任务流水线，中间 Agent 动作流，右侧实时证据库。过程透明，而不是一个模糊的 Loading。</p>
        </div>
        <span className="preview-pill">Execution Mock · 非真实工具调用</span>
      </div>

      <div className="tri-layout">
        <aside className="workflow-pipeline">
          <h3>任务流水线</h3>
          <div className="pipeline-tree">
            {mockPipeline.map((step) => (
              <div key={step.label} className={`pipeline-node ${step.status === "done" ? "done" : step.status === "active" ? "active" : ""}`}>
                <strong>{step.label}</strong><span>{step.detail}</span>
              </div>
            ))}
          </div>
          <div className="expert-team">
            <span className="expert-team-title">专家队 ({expertTeam.length})</span>
            <div className="expert-mini-group" aria-label="本次运行专家队">
              {expertTeam.map(([short, name]) => <span key={name} className="expert-mini" title={name}>{short}</span>)}
            </div>
          </div>
        </aside>

        <section className="agent-stream">
          <div className="agent-stream-head"><h3>Agent 动作流</h3><span className="status good">mock stream</span></div>
          <div className="stream-list">
            {mockAgentActions.map((action) => (
              <article key={action.agent} className="stream-item">
                <span className="stream-avatar">{actionShortName(action.agent)}</span>
                <div>
                  <div className="stream-meta">
                    <strong>{action.agent}</strong>
                    <span className={action.badge === "待验证" ? "chip warn" : "chip sage"}>{action.badge}</span>
                    <span className="stream-time">Mock step</span>
                  </div>
                  <p className="stream-content">{action.body}</p>
                </div>
              </article>
            ))}
          </div>
          <Link href={`/reports/${id}`} className="workflow-report-link">查看 Mock 报告 <ArrowRight aria-hidden="true" /></Link>
        </section>

        <aside className="workflow-side">
          <div className="trace-overview">
            <div className="trace-log-head"><h3>Agent 决策日志 · Trace</h3><span>Mock · 3 步</span></div>
            <div className="trace-list-mini">
              <article className="trace-step-mini">
                <span className="step-index">89</span>
                <div><span className="trace-step-title">需求理解 · 解析调研范围</span><div className="trace-step-meta"><span className="model-tag">默认模型</span><span>1,126 tokens</span></div></div>
              </article>
              <article className="trace-step-mini">
                <span className="step-index">90</span>
                <div><span className="trace-step-title">编排派遣 · 指派专家团队</span><div className="trace-step-meta"><span className="model-tag">默认模型</span><span>2,018 tokens</span></div></div>
                <div className="trace-expanded">
                  <div className="trace-raw-block"><strong>Prompt</strong><pre>基于用户确认的调研范围，拆解只读研究任务并选择合适专家。</pre></div>
                  <div className="trace-raw-block"><strong>Output</strong><pre>派遣证据采集、产品分析与定价策略专家；证据不足时标记 data_gap。</pre></div>
                </div>
              </article>
              <article className="trace-step-mini">
                <span className="step-index">91</span>
                <div><span className="trace-step-title">证据采集 · 生成 Evidence Pack</span><div className="trace-step-meta"><span className="model-tag">规则执行</span><span>0 tokens</span></div></div>
              </article>
            </div>
          </div>

          <div className="evidence-side-title"><h3>实时证据库</h3><span className="chip sage">Mock Evidence</span></div>
          <div className="evidence-list">
            {mockEvidence.map((evidence) => (
              <article key={evidence.id} className="evidence-card">
                <div className="evidence-top">
                  <div><h4>{evidence.title}</h4><span className="evidence-compact-meta">{evidence.source}</span></div>
                  <span className={evidence.level === "high" ? "chip sage" : "chip warn"}>{evidence.level === "high" ? "高置信" : "中置信"} {evidence.confidence}</span>
                </div>
                <p>{evidence.summary}</p>
                <a className="evidence-source-link" href={evidence.url} target="_blank" rel="noreferrer">查看来源 <ExternalLink aria-hidden="true" /></a>
              </article>
            ))}
          </div>
        </aside>
      </div>
    </section>
  );
}
