import Link from "next/link";

import { getApiData, toExpertCard } from "@/lib/api";

export const dynamic = "force-dynamic";

const layerTabs = ["全部", "L3 决策层", "L2 策略层", "L1 执行层"];

const expertMetaById = {
  research_orchestrator: [
    { icon: "route", text: "Research Plan" },
    { icon: "routing", text: "Expert Routing" },
    { icon: "memory", text: "Memory Read" }
  ],
  evidence_collector: [
    { icon: "search_check", text: "Search" },
    { icon: "link", text: "URL Intake" },
    { icon: "shield_alert", text: "Risk Notes" }
  ],
  product_analyst: [
    { icon: "layers", text: "Product Map" },
    { icon: "file_check", text: "Feature Pack" },
    { icon: "memory", text: "9 Memory" }
  ],
  pricing_analyst: [
    { icon: "web", text: "Web Search" },
    { icon: "memory", text: "12 Memory" },
    { icon: "schema", text: "Pricing JSON" }
  ],
  user_experience_analyst: [
    { icon: "message", text: "User Feedback" },
    { icon: "memory", text: "7 Memory" },
    { icon: "triangle", text: "Gap Control" }
  ],
  cross_validator: [
    { icon: "compare", text: "Cross Check" },
    { icon: "file_check", text: "Claim Pack" }
  ],
  qa_agent: [
    { icon: "shield_check", text: "QA Gate" },
    { icon: "rotate", text: "Rework 1x" }
  ],
  report_writer: [
    { icon: "file_pen", text: "Report Writer" },
    { icon: "book_check", text: "Evidence Only" }
  ]
};

function shortLayer(layer) {
  if (layer?.startsWith("L3")) return "L3 决策";
  if (layer?.startsWith("L2")) return "L2 策略";
  if (layer?.startsWith("L1")) return "L1 执行";
  return layer;
}

function metaFor(expert) {
  return expertMetaById[expert.id] || [
    { icon: "web", text: "Web Search" },
    { icon: "memory", text: "Memory" },
    { icon: "schema", text: expert.outputSchema }
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

  if (type === "search_check") {
    return (
      <svg viewBox="0 0 16 16" aria-hidden="true">
        <circle cx="7" cy="7" r="4.6" />
        <path d="m10.4 10.4 3 3" />
        <path d="M5 7.1 6.5 8.6 9.4 5.8" />
      </svg>
    );
  }

  if (type === "link") {
    return (
      <svg viewBox="0 0 16 16" aria-hidden="true">
        <path d="M6.6 9.4a3 3 0 0 0 4.2 0l1.8-1.8a3 3 0 0 0-4.2-4.2l-1 1" />
        <path d="M9.4 6.6a3 3 0 0 0-4.2 0L3.4 8.4a3 3 0 0 0 4.2 4.2l1-1" />
      </svg>
    );
  }

  if (type === "shield_alert" || type === "shield_check") {
    return (
      <svg viewBox="0 0 16 16" aria-hidden="true">
        <path d="M8 2.2 13 4v3.7c0 3-1.9 5.2-5 6.1-3.1-.9-5-3.1-5-6.1V4z" />
        {type === "shield_check" ? <path d="M5.7 8.1 7.2 9.6 10.4 6.4" /> : <path d="M8 5.5v3M8 11h.1" />}
      </svg>
    );
  }

  if (type === "message") {
    return (
      <svg viewBox="0 0 16 16" aria-hidden="true">
        <path d="M3 3.2h10v7.2H7L3 13z" />
        <path d="M5.5 6h5M5.5 8.2h3.8" />
      </svg>
    );
  }

  if (type === "triangle") {
    return (
      <svg viewBox="0 0 16 16" aria-hidden="true">
        <path d="M8 2.6 14 13H2z" />
        <path d="M8 6.2v3.2M8 11.6h.1" />
      </svg>
    );
  }

  if (type === "compare") {
    return (
      <svg viewBox="0 0 16 16" aria-hidden="true">
        <path d="M3 5h9.5" />
        <path d="m10.4 2.9 2.1 2.1-2.1 2.1" />
        <path d="M13 11H3.5" />
        <path d="m5.6 8.9-2.1 2.1 2.1 2.1" />
      </svg>
    );
  }

  if (type === "file_check" || type === "file_pen") {
    return (
      <svg viewBox="0 0 16 16" aria-hidden="true">
        <path d="M4 2.4h5.3L12 5.1v8.5H4z" />
        <path d="M9.3 2.4v2.7H12" />
        {type === "file_check" ? <path d="M5.8 9 7.1 10.3 10 7.4" /> : <path d="M6 10.8 9.8 7l1.2 1.2-3.8 3.8H6z" />}
      </svg>
    );
  }

  if (type === "rotate") {
    return (
      <svg viewBox="0 0 16 16" aria-hidden="true">
        <path d="M4.1 5.5A5 5 0 1 1 4 10.3" />
        <path d="M4.1 2.8v2.7h2.7" />
      </svg>
    );
  }

  if (type === "book_check") {
    return (
      <svg viewBox="0 0 16 16" aria-hidden="true">
        <path d="M3 3.2h4.2c.8 0 1.4.6 1.4 1.4v8.2c0-.8-.6-1.4-1.4-1.4H3z" />
        <path d="M13 3.2H8.8c-.8 0-1.4.6-1.4 1.4v8.2c0-.8.6-1.4 1.4-1.4H13z" />
        <path d="M9.1 8.2 10.4 9.5 12.6 7.3" />
      </svg>
    );
  }

  if (type === "route" || type === "routing") {
    return (
      <svg viewBox="0 0 16 16" aria-hidden="true">
        <circle cx="4" cy="4" r="1.6" />
        <circle cx="12" cy="12" r="1.6" />
        <path d="M5.6 4h2.7A2.7 2.7 0 0 1 11 6.7v0A2.7 2.7 0 0 1 8.3 9.4H7.7A2.7 2.7 0 0 0 5 12.1v0" />
      </svg>
    );
  }

  if (type === "layers") {
    return (
      <svg viewBox="0 0 16 16" aria-hidden="true">
        <path d="M8 2.5 13.5 5.5 8 8.5 2.5 5.5z" />
        <path d="m2.5 8 5.5 3 5.5-3" />
        <path d="m2.5 10.5 5.5 3 5.5-3" />
      </svg>
    );
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
