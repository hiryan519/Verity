import { BarChart3, FileSearch, Network, UsersRound } from "lucide-react";

const modules = [
  { Icon: FileSearch, title: "报告概览", body: "等待真实报告与结构化结论数据接入。" },
  { Icon: Network, title: "信源结构", body: "只展示可复查证据的来源分布，不生成装饰性图表。" },
  { Icon: UsersRound, title: "专家贡献", body: "后续基于真实 Trace 统计专家参与与阶段产出。" }
];

export default function IntelligencePage() {
  return (
    <section className="asset-page route-section">
      <div className="section-head">
        <div>
          <p className="eyebrow">Competitive Intelligence</p>
          <h2>竞争情报中心</h2>
          <p>聚合跨报告的结构化研究信号。指标必须来自可复查证据、报告和 Trace，不能用 Mock 图表暗示真实市场趋势。</p>
        </div>
        <span className="preview-pill">P1 占位 · 暂无真实指标</span>
      </div>

      <div className="intelligence-strip">
        <BarChart3 aria-hidden="true" />
        <div><strong>等待结构化数据接入</strong><span>当前只建立页面信息边界，不展示无法解释的增长率、舆情规模或市场份额。</span></div>
      </div>

      <div className="intelligence-grid">
        {modules.map(({ Icon, title, body }) => (
          <article key={title} className="intelligence-card"><Icon aria-hidden="true" /><h3>{title}</h3><p>{body}</p><span>待接入</span></article>
        ))}
      </div>
    </section>
  );
}
