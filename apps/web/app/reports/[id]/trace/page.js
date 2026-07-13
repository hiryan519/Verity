import { Panel, SectionTitle } from "@/components/ui";
import { getApiData } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function TracePage({ params }) {
  const { id } = await params;
  const { item, dataSource, error } = await getApiData(`/api/reports/${id}`);
  const traceSteps = item?.trace_steps || [];
  const totalToken = traceSteps.reduce((sum, step) => sum + (step.token_count || 0), 0);
  const totalDuration = traceSteps.reduce((sum, step) => sum + (step.duration_ms || 0), 0);
  const sourceLabel = dataSource ? `${dataSource.mode} · ${dataSource.seed || "evolva"}` : "API 未连接";

  return (
    <div>
      <SectionTitle
        eyebrow="Decision Trace"
        title="决策链路"
        description="展示用户可理解、已脱敏、可审计的关键 Trace。这里不是原始日志倾倒，也没有展示敏感凭据。"
        badge={`trace ${id}`}
      />

      <div className="grid gap-4 lg:grid-cols-[280px_minmax(0,1fr)]">
        <Panel title="阶段筛选" meta={sourceLabel}>
          {error ? <p className="mb-3 text-sm text-[color:var(--warning)]">API 未连接：{error}</p> : null}
          <div className="timeline">
            {traceSteps.map((step) => (
              <div key={step.id} className={`timeline-step ${step.status === "done" || step.status === "completed" ? "done" : "warn"}`}>
                <strong className="text-sm">{step.stage}</strong>
                <span className="text-xs text-black/55">{step.agent} · {step.duration_ms}ms</span>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Trace Step 展开" meta="sanitized">
          <div className="grid gap-3 md:grid-cols-3">
            <div className="panel p-4"><span className="text-xs text-[color:var(--muted)]">Total Token</span><strong className="mt-2 block text-2xl">{totalToken}</strong></div>
            <div className="panel p-4"><span className="text-xs text-[color:var(--muted)]">Duration</span><strong className="mt-2 block text-2xl">{Math.round(totalDuration / 1000)}s</strong></div>
            <div className="panel p-4"><span className="text-xs text-[color:var(--muted)]">Steps</span><strong className="mt-2 block text-2xl">{traceSteps.length}</strong></div>
          </div>

          <div className="mt-4 grid gap-3">
            {traceSteps.map((step) => (
              <article key={step.id} className="panel p-4">
                <div className="mb-3 flex items-start justify-between">
                  <div>
                    <h3 className="text-sm font-semibold">{step.agent} · {step.stage}</h3>
                    <p className="mt-1 text-xs text-[color:var(--muted)]">status: {step.status} · model: {step.model}</p>
                  </div>
                  <span className={step.status === "done" || step.status === "completed" ? "chip chip-sage" : "chip chip-warning"}>{step.status}</span>
                </div>
                <p className="body-copy m-0 text-sm">{step.task}</p>
                <pre className="mt-3 overflow-auto rounded-xl border border-[color:var(--line)] bg-[color:var(--workspace)] p-3 text-xs leading-6 text-black/65">{JSON.stringify({
                  prompt: step.prompt,
                  input: step.input,
                  output: step.output,
                  related_evidence: step.evidence_ids,
                  related_report_sections: step.report_sections
                }, null, 2)}</pre>
              </article>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}
