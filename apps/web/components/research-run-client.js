"use client";

import Link from "next/link";
import { ArrowRight, CircleAlert, ExternalLink, FileText, LoaderCircle, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { getApiData, postApiData } from "@/lib/api";

const stages = [
  ["scope", "范围确认", "Human Gate 已确认"],
  ["evidence", "证据采集", "公开网页与用户 URL"],
  ["experts", "专家分析", "按维度并行执行"],
  ["cross", "交叉验证", "检查冲突与数据缺口"],
  ["qa", "QA 质检", "判断是否允许交付"],
  ["report", "报告交付", "仅使用通过的 Analysis Pack"]
];

function statusLabel(status) {
  if (status === "done") return "已完成";
  if (status === "active") return "执行中";
  if (status === "warn") return "需关注";
  return "等待";
}

function stageState(stage, item, detail, started) {
  if (stage === "scope") return "done";
  if (!started) return "pending";
  if (stage === "evidence") return detail?.evidence?.length ? "done" : item?.collection ? "warn" : "active";
  if (stage === "experts") return item?.analysis_pack ? "done" : item?.status === "running" ? "active" : "pending";
  if (stage === "cross") return item?.analysis_pack?.cross_validation_pack || item?.cross_validation ? "done" : item?.status === "completed" ? "warn" : "pending";
  if (stage === "qa") {
    const verdict = item?.qa_gate?.verdict || detail?.qa_gate?.verdict;
    if (verdict === "rework") return "warn";
    if (verdict === "pass" || verdict === "pass_with_risk") return "done";
    return item?.status === "completed" ? "warn" : "active";
  }
  if (stage === "report") {
    if (detail?.report_artifact) return "done";
    if ((item?.qa_gate?.verdict || detail?.qa_gate?.verdict) === "rework") return "warn";
    return "pending";
  }
  return "pending";
}

function shortAgent(agent = "Agent") {
  if (agent.includes("QA")) return "QA";
  if (agent.includes("证据")) return "证";
  if (agent.includes("定价")) return "价";
  if (agent.includes("产品")) return "产";
  if (agent.includes("用户")) return "体";
  if (agent.includes("交叉")) return "验";
  if (agent.includes("报告")) return "撰";
  return agent.slice(0, 1);
}

function readable(value) {
  if (typeof value === "string") return value;
  return JSON.stringify(value ?? {}, null, 2);
}

export function ResearchRunClient({ runId }) {
  const autoStarted = useRef(false);
  const [started, setStarted] = useState(false);
  const [runOptions, setRunOptions] = useState({ urls: [] });
  const [loading, setLoading] = useState(false);
  const [workflow, setWorkflow] = useState(null);
  const [detail, setDetail] = useState(null);
  const [error, setError] = useState("");

  const loadDetail = useCallback(async () => {
    const response = await getApiData(`/api/reports/${runId}`);
    if (response.error) setError(response.error);
    setDetail(response.item || null);
    return response.item;
  }, [runId]);

  const runResearch = useCallback(async (providedUrls = runOptions.urls) => {
    setLoading(true);
    setStarted(true);
    setError("");
    const response = await postApiData(`/api/research/runs/${runId}/run`, {
      queries: [],
      user_urls: providedUrls,
      dimensions: [],
      scope_overrides: {},
      max_results: 5,
      include_domains: [],
      exclude_domains: []
    });
    setWorkflow(response);
    if (response.error) {
      setError(response.error);
      setLoading(false);
      return;
    }

    const item = response.item;
    const verdict = item?.qa_gate?.verdict;
    if (verdict === "pass" || verdict === "pass_with_risk") {
      const writerResponse = await postApiData(`/api/llm/reports/${runId}/write`, { report_outline: {} });
      setWorkflow((current) => ({ ...current, writer: writerResponse }));
      if (writerResponse.error) setError(writerResponse.error);
    }
    await loadDetail();
    setLoading(false);
  }, [loadDetail, runId, runOptions.urls]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urls = (params.get("urls") || "").split(",").map((url) => url.trim()).filter(Boolean);
    setRunOptions({ urls });
    if (params.get("auto") === "1" && !autoStarted.current) {
      autoStarted.current = true;
      runResearch(urls);
    }
  }, [runResearch]);

  const item = workflow?.item;
  const qaVerdict = item?.qa_gate?.verdict || detail?.qa_gate?.verdict || detail?.qa_status;
  const traceSteps = detail?.trace_steps || [];
  const evidence = detail?.evidence || [];
  const isReal = workflow?.data_source?.is_real_research || detail?.data_source?.is_real_research;
  const currentStatus = loading ? "正在执行真实研究…" : qaVerdict === "rework" ? "QA 返工" : workflow ? "研究链路已返回" : "等待开始";

  const stream = useMemo(() => {
    if (traceSteps.length) return traceSteps.slice(-8).map((step) => ({
      id: step.id,
      agent: step.agent || "Agent",
      status: step.status || "completed",
      time: `${step.token_count || 0} tokens · ${((step.duration_ms || 0) / 1000).toFixed(1)}s`,
      body: step.task || step.stage || "阶段执行完成"
    }));
    if (item?.analysis_pack) return [{ id: "pack", agent: "研究 Workflow", status: "completed", time: "真实结构化结果", body: "Evidence 已汇聚为 Analysis Pack，并进入 QA Gate。" }];
    return [];
  }, [item, traceSteps]);

  return (
    <section className="workflow-page route-section">
      <div className="section-head">
        <div>
          <p className="eyebrow">Agent Workflow</p>
          <h2>调研执行页</h2>
          <p>本页展示同一个真实 Run 的证据采集、专家分析、QA 和 Trace。未开始时不填充 Mock 动作。</p>
        </div>
        <span className={`preview-pill ${isReal ? "real-pill" : ""}`}>{isReal ? "真实在线 Run" : workflow ? "local workflow" : "等待执行"}</span>
      </div>

      <div className="workflow-run-toolbar">
        <div><span className="workflow-run-id">Run ID · {runId}</span><span className="workflow-run-status">{currentStatus}</span></div>
        <button type="button" className="soft-button" onClick={runResearch} disabled={loading}><RefreshCw aria-hidden="true" />{loading ? "执行中" : workflow ? "重新执行" : "开始真实调研"}</button>
      </div>

      {error ? <p className="form-error" role="alert">{error}</p> : null}

      <div className="tri-layout">
        <aside className="workflow-pipeline">
          <h3>任务流水线</h3>
          <div className="pipeline-tree">
            {stages.map(([id, label, detailText]) => {
              const state = stageState(id, item, detail, started);
              return <div key={id} className={`pipeline-node ${state}`}><strong>{label}</strong><span>{state === "warn" && id === "qa" ? `QA ${qaVerdict}` : state === "done" ? "已写入真实 Run" : detailText}</span></div>;
            })}
          </div>
          <div className="expert-team"><span className="expert-team-title">真实数据边界</span><p className="workflow-boundary-copy">公开网页 + 用户 URL。搜索摘要不会直接作为 Evidence。</p></div>
        </aside>

        <section className="agent-stream">
          <div className="agent-stream-head"><h3>Agent 动作流</h3><span className={`status ${loading ? "good" : qaVerdict === "rework" ? "warn" : "good"}`}>{loading ? "running" : workflow ? "real result" : "not started"}</span></div>
          {!stream.length ? <div className="workflow-empty"><LoaderCircle aria-hidden="true" /><strong>{loading ? "专家正在处理证据…" : "尚未执行真实 Run"}</strong><p>{loading ? "Tavily 采集与专家链路完成后，这里会显示真实阶段成果。" : "点击右上角开始调研，不会使用静态 Mock 动作。"}</p></div> : <div className="stream-list">{stream.map((action) => <article key={action.id} className="stream-item"><span className="stream-avatar">{shortAgent(action.agent)}</span><div><div className="stream-meta"><strong>{action.agent}</strong><span className={action.status === "failed" ? "chip warn" : "chip sage"}>{action.status}</span><span className="stream-time">{action.time}</span></div><p className="stream-content">{action.body}</p></div></article>)}</div>}
          {detail?.report_artifact ? <Link href={`/reports/${runId}`} className="workflow-report-link">查看真实报告 <ArrowRight aria-hidden="true" /></Link> : <span className="workflow-report-disabled"><FileText aria-hidden="true" />{qaVerdict === "rework" ? "报告暂未签发：等待返工或人工确认" : "报告将在 QA 通过后签发"}</span>}
        </section>

        <aside className="workflow-side">
          <div className="trace-overview"><div className="trace-log-head"><h3>真实证据与 Trace</h3><span>{traceSteps.length} 步</span></div><div className="trace-list-mini">{traceSteps.slice(-3).map((step, index) => <article key={step.id || index} className="trace-step-mini"><span className="step-index">{String(traceSteps.length - 2 + index).padStart(2, "0")}</span><div><span className="trace-step-title">{step.stage || "执行阶段"} · {step.task || step.agent}</span><div className="trace-step-meta"><span className="model-tag">{step.model || "未记录模型"}</span><span>{step.token_count || 0} tokens</span></div></div></article>)}</div>{traceSteps.length ? <Link href={`/reports/${runId}/trace`} className="trace-detail-link">打开完整决策链路 <ArrowRight aria-hidden="true" /></Link> : null}</div>
          <div className="evidence-side-title"><h3>Evidence Store</h3><span className={`chip ${evidence.length ? "sage" : "warn"}`}>{evidence.length} 条</span></div>
          {!evidence.length ? <div className="evidence-empty"><CircleAlert aria-hidden="true" />{loading ? "正在读取公开网页…" : "尚未取得可用 Evidence"}</div> : <div className="evidence-list">{evidence.slice(0, 8).map((evidenceItem) => <article key={evidenceItem.id} className="evidence-card" id={`evidence-${evidenceItem.id}`}><div className="evidence-top"><div><h4>{evidenceItem.title}</h4><span className="evidence-compact-meta">{evidenceItem.source_label || evidenceItem.platform} · {evidenceItem.captured_at}</span></div><span className={evidenceItem.confidence_level === "high" ? "chip sage" : "chip warn"}>{evidenceItem.confidence_level} {evidenceItem.confidence}</span></div><p>{evidenceItem.summary}</p>{evidenceItem.risk_note ? <span className="evidence-risk">风险：{evidenceItem.risk_note}</span> : null}{evidenceItem.url ? <a className="evidence-source-link" href={evidenceItem.url} target="_blank" rel="noreferrer">打开来源 <ExternalLink aria-hidden="true" /></a> : null}</article>)}</div>}
          {workflow?.item?.qa_gate ? <div className={`qa-result ${qaVerdict === "rework" ? "warn" : ""}`}><strong>QA Gate · {qaVerdict}</strong><span>{workflow.item.qa_gate.total_score ?? "-"} 分 · 返工 {workflow.item.qa_gate.rework_count ?? 0} 次</span></div> : null}
          {workflow?.item?.qa_gate?.issues?.length ? <div className="qa-issues"><strong>需要处理</strong>{workflow.item.qa_gate.issues.slice(0, 3).map((issue, index) => <p key={`${issue}-${index}`}>{issue}</p>)}</div> : null}
        </aside>
      </div>
    </section>
  );
}
