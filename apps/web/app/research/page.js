import Link from "next/link";
import { ArrowUpRight, GitBranch } from "lucide-react";
import { getApiData, toReportCard } from "@/lib/api";

export const dynamic = "force-dynamic";

function statusMeta(status) {
  if (status === "pass") return { label: "已完成", className: "chip sage" };
  if (status === "risk" || status === "pass_with_risk") return { label: "带风险", className: "chip warn" };
  return { label: "草稿", className: "chip sage" };
}

export default async function ResearchListPage() {
  const { dataSource, items, error } = await getApiData("/api/reports");
  const reports = items.map(toReportCard);

  return (
    <section className="research-page route-section">
      <div className="section-head">
        <div>
          <p className="eyebrow">Research Assets</p>
          <h2>我的调研</h2>
          <p>历史报告是可持续复查的研究资产，不等同于 Research Memory。每份报告拥有稳定访问路径，并保留报告与决策链路入口。</p>
        </div>
        <span className="preview-pill">{dataSource ? `${dataSource.mode} · ${dataSource.seed}` : "API 未连接"}</span>
      </div>

      {error ? <p className="asset-notice">API 未连接：{error}</p> : null}
      <div className="research-grid">
        {reports.map((report) => {
          const status = statusMeta(report.qaStatus);
          return (
            <article key={report.id} className="research-card">
              <div className="research-card-top"><span className={status.className}>{status.label}</span><span>{report.updatedAt}</span></div>
              <h3>{report.title}</h3>
              <p>{report.summary}</p>
              <div className="research-card-stats"><span>{report.evidenceCount} 条证据</span><span>{report.claimCount} 个结论</span><span>{report.highConfidenceCount} 个高置信</span></div>
              <div className="research-card-actions">
                <Link href={`/reports/${report.id}`}>打开报告 <ArrowUpRight aria-hidden="true" /></Link>
                <Link href={`/reports/${report.id}/trace`}><GitBranch aria-hidden="true" />决策链路</Link>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
