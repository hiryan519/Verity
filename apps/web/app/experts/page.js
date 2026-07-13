import Link from "next/link";

import { getApiData, toExpertCard } from "@/lib/api";

export const dynamic = "force-dynamic";

const layerTabs = ["全部", "L3 决策层", "L2 策略层", "L1 执行层"];

function shortLayer(layer) {
  if (layer?.startsWith("L3")) return "L3 决策";
  if (layer?.startsWith("L2")) return "L2 策略";
  if (layer?.startsWith("L1")) return "L1 执行";
  return layer;
}

function metaFor(expert) {
  return [
    expert.supportsMultiInstance ? "支持多实例" : "单实例",
    "治理只读",
    expert.outputSchema
  ];
}

export default async function ExpertsPage() {
  const { dataSource, items, error } = await getApiData("/api/experts");
  const experts = items.map(toExpertCard);
  const badge = dataSource ? `${dataSource.mode} · ${dataSource.seed}` : "API 未连接";

  return (
    <div className="expert-page-shell">
      <section className="expert-hero">
        <div>
          <p className="eyebrow">Expert Agent Library</p>
          <h1>专家公会</h1>
          <p>
            专家公会展示 Verity 的 Expert Agent Registry 与治理信息。这里看职责、边界、工具授权、输出结构和运行约束，不在页面自由编辑 Prompt。
          </p>
        </div>
        <span className="chip chip-sage">{badge}</span>
      </section>

      {error ? <p className="mb-3 text-sm text-[color:var(--warning)]">API 未连接：{error}</p> : null}

      <div className="expert-toolbar">
        <label className="expert-search">
          <span>⌕</span>
          <input aria-label="搜索专家" placeholder="搜索专家、工具或输出结构" />
        </label>
        <div className="expert-tabs" aria-label="专家层级筛选">
          {layerTabs.map((tab, index) => (
            <span key={tab} className={index === 0 ? "active" : ""}>
              {tab}
            </span>
          ))}
        </div>
      </div>

      <div className="expert-card-grid">
        {experts.map((expert) => (
          <Link key={expert.id} href={`/experts/${expert.id}`} className="expert-card">
            <div>
              <div className="expert-card-head">
                <h2>{expert.name}</h2>
                <span className="level-badge">{shortLayer(expert.layer)}</span>
              </div>
              <p>{expert.role}</p>
            </div>

            <div className="expert-meta-tags">
              {metaFor(expert).map((meta) => (
                <span key={meta}>{meta}</span>
              ))}
            </div>

            <div className="expert-model-row">
              <span>默认模型</span>
              <span className="model-pill">默认模型</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
