import { SectionTitle } from "@/components/ui";
import { getApiData, toExpertCard } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ExpertsPage() {
  const { dataSource, items, error } = await getApiData("/api/experts");
  const experts = items.map(toExpertCard);
  const badge = dataSource ? `${dataSource.mode} · ${dataSource.seed} seed` : "API 未连接";

  return (
    <div>
      <SectionTitle
        eyebrow="Expert Agent Library"
        title="专家公会"
        description="专家是可被 Orchestrator 调度的任务型 Agent，不是单纯 Skill。每个专家都有目标、工具边界、输出 Schema 和 Trace。"
        badge={badge}
      />

      {error ? <p className="mb-3 text-sm text-[color:var(--warning)]">API 未连接：{error}</p> : null}
      <div className="grid-3">
        {experts.map((expert) => (
          <article key={expert.id} className="panel p-4">
            <span className="chip chip-sage">{expert.layer}</span>
            <h2 className="card-title mt-4">{expert.name}</h2>
            <p className="mt-3 text-sm leading-6 text-black/60">{expert.role}</p>
            <div className="mt-4 border-t border-[color:var(--line)] pt-4 text-xs leading-6 text-black/55">
              <div>Tool scope: {expert.tools.join(", ")}</div>
              <div>Output: {expert.outputSchema}</div>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
