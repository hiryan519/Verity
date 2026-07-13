import Link from "next/link";
import { SectionTitle } from "@/components/ui";
import { getApiData, toReportCard } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ResearchListPage() {
  const { dataSource, items, error } = await getApiData("/api/reports");
  const reports = items.map(toReportCard);
  const badge = dataSource ? `${dataSource.mode} · ${dataSource.seed} seed` : "API 未连接";

  return (
    <div>
      <SectionTitle
        eyebrow="Research Assets"
        title="我的调研"
        description="历史报告是研究资产，不等同于 Memory。当前从本地 SQLite 读取 mock seed 数据，仍未接入真实 Agent Workflow。"
        badge={badge}
      />

      {error ? <p className="mb-3 text-sm text-[color:var(--warning)]">API 未连接：{error}</p> : null}
      <div className="grid-3">
        {reports.map((report) => (
          <article key={report.id} className="panel p-4">
            <span className={report.qaStatus === "pass" ? "chip chip-sage" : report.qaStatus === "risk" ? "chip chip-warning" : "chip chip-sage"}>{report.qaStatus}</span>
            <h2 className="card-title mt-4">{report.title}</h2>
            <p className="mt-2 text-sm leading-6 text-black/60">{report.summary}</p>
            <div className="mt-4 grid grid-cols-3 gap-2 text-xs text-black/55">
              <span>证据 {report.evidenceCount}</span>
              <span>结论 {report.claimCount}</span>
              <span>高可信 {report.highConfidenceCount}</span>
            </div>
            <div className="mt-4 flex gap-2">
              <Link href={`/reports/${report.id}`} className="btn btn-primary">报告</Link>
              <Link href={`/reports/${report.id}/trace`} className="btn btn-secondary">Trace</Link>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
