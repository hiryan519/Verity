import Link from "next/link";
import {
  BookOpenCheck,
  Braces,
  Cpu,
  Database,
  FileCheck2,
  FilePenLine,
  GitBranch,
  GitCompareArrows,
  Globe2,
  Layers,
  Link2,
  MessageSquareText,
  RotateCcw,
  Route,
  SearchCheck,
  ShieldAlert,
  ShieldCheck,
  TriangleAlert
} from "lucide-react";

import { getApiData, toExpertCard } from "@/lib/api";

export const dynamic = "force-dynamic";

const layerTabs = ["全部", "L3 决策层", "L2 策略层", "L1 执行层"];

const expertMetaById = {
  research_orchestrator: [
    { Icon: Route, text: "Research Plan" },
    { Icon: GitBranch, text: "Expert Routing" },
    { Icon: Database, text: "Memory Read" }
  ],
  evidence_collector: [
    { Icon: SearchCheck, text: "Search" },
    { Icon: Link2, text: "URL Intake" },
    { Icon: ShieldAlert, text: "Risk Notes" }
  ],
  product_analyst: [
    { Icon: Layers, text: "Product Map" },
    { Icon: FileCheck2, text: "Feature Pack" },
    { Icon: Database, text: "9 Memory" }
  ],
  pricing_analyst: [
    { Icon: Globe2, text: "Web Search" },
    { Icon: Database, text: "12 Memory" },
    { Icon: Braces, text: "Pricing JSON" }
  ],
  user_experience_analyst: [
    { Icon: MessageSquareText, text: "User Feedback" },
    { Icon: Database, text: "7 Memory" },
    { Icon: TriangleAlert, text: "Gap Control" }
  ],
  cross_validator: [
    { Icon: GitCompareArrows, text: "Cross Check" },
    { Icon: FileCheck2, text: "Claim Pack" }
  ],
  qa_agent: [
    { Icon: ShieldCheck, text: "QA Gate" },
    { Icon: RotateCcw, text: "Rework 1x" }
  ],
  report_writer: [
    { Icon: FilePenLine, text: "Report Writer" },
    { Icon: BookOpenCheck, text: "Evidence Only" }
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
    { Icon: Globe2, text: "Web Search" },
    { Icon: Database, text: "Memory" },
    { Icon: Braces, text: expert.outputSchema }
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
                <span key={meta.text}>
                  <meta.Icon aria-hidden="true" />
                  {meta.text}
                </span>
              ))}
            </div>

            <div className="expert-model-row">
              <span>当前模型</span>
              <span className="model-pill">
                <Cpu aria-hidden="true" />
                默认模型
              </span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
