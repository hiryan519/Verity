import Link from "next/link";
import { SectionTitle } from "@/components/ui";
import { getApiData, toReportCard } from "@/lib/api";

export const dynamic = "force-dynamic";

const examples = [
  "分析 Notion AI、飞书妙记、Gamma 在 AI 协作写作场景下的产品策略",
  "比较 Linear、Jira、Asana 的团队协作和定价边界",
  "研究 Gamma、Tome、Canva AI 的生成式演示工具定位"
];

export default async function WorkspacePage() {
  const { dataSource, items, error } = await getApiData("/api/reports");
  const reports = items.map(toReportCard);
  const sourceLabel = dataSource ? `${dataSource.mode} · ${dataSource.seed} seed` : "API 未连接";

  return (
    <div>
      <SectionTitle
        eyebrow="Workspace"
        title="让竞品研究像证据档案一样可读、可复查、可追溯。"
        description="输入一个研究目标，Verity 先进入调研范围确认，再由 Orchestrator 调度专家 Agent。当前阶段为 Mock 产品形态，未接入真实在线抓取。"
        badge="Mock workflow"
      />

      <section className="panel p-5">
        <textarea
          className="min-h-[128px] w-full resize-y border-0 bg-transparent font-editorial text-base leading-8 outline-none placeholder:text-black/35"
          placeholder="例如：分析 Notion AI、飞书妙记、Gamma 在 AI 协作写作场景下的产品策略、定价与用户反馈差异"
        />
        <div className="mt-4 flex items-center justify-between border-t border-[color:var(--line)] pt-4">
          <span className="text-xs text-[color:var(--muted)]">数据源：{sourceLabel} · 不代表真实抓取</span>
          <Link href="/research/new" className="btn btn-primary">确认调研范围</Link>
        </div>
      </section>

      <div className="mt-4 grid-3">
        {examples.map((example) => (
          <Link key={example} href="/research/new" className="panel p-4">
            <h2 className="card-title">{example}</h2>
            <p className="mt-3 text-sm leading-6 text-black/60">进入 Human Gate 后再确认竞品、维度、市场和时间范围。</p>
          </Link>
        ))}
      </div>

      <section className="mt-10">
        <h2 className="mb-3 text-sm font-semibold">最近调研</h2>
        {error ? <p className="mb-3 text-sm text-[color:var(--warning)]">API 未连接：{error}</p> : null}
        <div className="grid-3">
          {reports.map((report) => (
            <Link key={report.id} href={`/reports/${report.id}`} className="panel p-4">
              <span className="chip chip-sage">{report.qaStatus}</span>
              <h3 className="card-title mt-4">{report.title}</h3>
              <p className="mt-3 text-sm leading-6 text-black/60">{report.summary}</p>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
