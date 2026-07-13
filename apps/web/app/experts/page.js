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

function metaFor() {
  return [
    { icon: "web", text: "Web Search" },
    { icon: "memory", text: "12 Memory" },
    { icon: "schema", text: "Pricing JSON" }
  ];
}

function MetaIcon({ type }) {
  if (type === "memory") {
    return (
      <svg viewBox="0 0 16 16" aria-hidden="true">
        <ellipse cx="8" cy="3.6" rx="5.2" ry="2.1" />
        <path d="M2.8 3.6v4.2c0 1.2 2.3 2.1 5.2 2.1s5.2-.9 5.2-2.1V3.6" />
        <path d="M2.8 7.8V12c0 1.2 2.3 2.1 5.2 2.1s5.2-.9 5.2-2.1V7.8" />
      </svg>
    );
  }

  if (type === "schema") {
    return <span className="meta-braces" aria-hidden="true">{"{}"}</span>;
  }

  return (
    <svg viewBox="0 0 16 16" aria-hidden="true">
      <circle cx="8" cy="8" r="6" />
      <path d="M2.5 7.4h11" />
      <path d="M8 2.2c1.5 1.5 2.2 3.4 2.2 5.8s-.7 4.3-2.2 5.8C6.5 12.3 5.8 10.4 5.8 8s.7-4.3 2.2-5.8Z" />
    </svg>
  );
}

function ModelIcon() {
  return (
    <svg viewBox="0 0 16 16" aria-hidden="true">
      <rect x="4" y="4" width="8" height="8" rx="1.4" />
      <path d="M1.8 6h2.2M1.8 10h2.2M12 6h2.2M12 10h2.2M6 1.8v2.2M10 1.8v2.2M6 12v2.2M10 12v2.2" />
      <circle cx="8" cy="8" r="1.5" />
    </svg>
  );
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
                <span key={meta.text}>
                  <MetaIcon type={meta.icon} />
                  {meta.text}
                </span>
              ))}
            </div>

            <div className="expert-model-row">
              <span>当前模型</span>
              <span className="model-pill">
                <ModelIcon />
                默认模型
              </span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
