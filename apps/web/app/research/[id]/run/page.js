import Link from "next/link";
import { mockAgentActions, mockEvidence, mockPipeline } from "@/lib/mock-data";
import { ConfidenceChip, Panel, SectionTitle } from "@/components/ui";

export default function ResearchRunPage({ params }) {
  return (
    <div>
      <SectionTitle
        eyebrow="Agent Workflow"
        title="调研执行"
        description="左侧任务流水线，中间 Agent 动作流，右侧实时证据库。当前为 Mock 执行过程，不代表真实工具调用。"
        badge={`report ${params.id}`}
      />

      <div className="three-column">
        <Panel title="任务流水线" meta="P0 flow">
          <div className="timeline">
            {mockPipeline.map((step) => (
              <div key={step.label} className={`timeline-step ${step.status === "done" ? "done" : step.status === "active" ? "active" : step.status === "warn" ? "warn" : ""}`}>
                <strong className="text-sm">{step.label}</strong>
                <span className="text-xs leading-5 text-black/55">{step.detail}</span>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Agent 动作流" meta="Mock actions">
          <div className="grid gap-3">
            {mockAgentActions.map((action) => (
              <article key={action.agent} className="panel p-4">
                <div className="mb-3 flex items-start justify-between gap-3">
                  <div>
                    <h3 className="text-sm font-semibold">{action.agent}</h3>
                    <span className="text-xs text-[color:var(--muted)]">工具边界：公开网页 / 用户 URL / 上传文件</span>
                  </div>
                  <span className="chip chip-sage">{action.badge}</span>
                </div>
                <p className="body-copy m-0">{action.body}</p>
              </article>
            ))}
          </div>
        </Panel>

        <Panel title="实时证据库" meta="Mock evidence">
          <div className="grid gap-3">
            {mockEvidence.map((evidence) => (
              <article key={evidence.id} className="panel p-4">
                <div className="mb-3 flex items-start justify-between gap-3">
                  <div>
                    <h3 className="text-sm font-semibold">{evidence.title}</h3>
                    <span className="text-xs text-[color:var(--muted)]">{evidence.source}</span>
                  </div>
                  <ConfidenceChip score={evidence.confidence} level={evidence.level === "high" ? "high" : "medium"} />
                </div>
                <p className="body-copy m-0 text-sm">{evidence.summary}</p>
              </article>
            ))}
          </div>
        </Panel>
      </div>

      <div className="mt-5 flex justify-end">
        <Link href={`/reports/${params.id}`} className="btn btn-primary">查看 Mock 报告</Link>
      </div>
    </div>
  );
}
