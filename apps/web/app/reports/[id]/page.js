import Link from "next/link";
import {
  BadgeCheck, BookMarked, BookOpen, BookmarkPlus, Clock3, FileText, GitBranch,
  Globe2, Link2, MessageSquare, Network, ShieldCheck, SlidersHorizontal, Sparkles, TriangleAlert, Users
} from "lucide-react";
import { mockEvidence } from "@/lib/mock-data";

const sections = [
  { id: "summary", index: "01", label: "执行摘要" },
  { id: "positioning", index: "02", label: "产品定位" },
  { id: "pricing", index: "03", label: "定价策略" },
  { id: "voice", index: "04", label: "用户体验" },
  { id: "risk", index: "05", label: "数据缺口与风险" }
];

function ChapterFooter({ sources, action, note }) {
  return (
    <div className="chapter-footer">
      <div className="chapter-source-row">
        <span className="chapter-source-head"><Link2 aria-hidden="true" />本章信源</span>
        <div className="source-pills">{sources.map((source) => <button key={source} className="source-pill">[{source}]</button>)}</div>
      </div>
      {action ? <div className="chapter-action-row"><button className="chapter-action"><Sparkles aria-hidden="true" />{action}</button><span>{note}</span></div> : null}
    </div>
  );
}

export default async function ReportPage({ params }) {
  const { id } = await params;

  return (
    <section className="report-reader">
      <aside className="reader-toc">
        <span className="reader-toc-title">目录</span>
        <div className="progress-row" aria-label="阅读进度"><div className="reading-progress"><span /></div><span className="progress-value">12%</span></div>
        <nav aria-label="报告目录">
          {sections.map((section, index) => (
            <a key={section.id} className={index === 0 ? "active" : ""} href={`#${section.id}`}>
              <span className="toc-index">{section.index}</span><span>{section.label}</span>
            </a>
          ))}
        </nav>
      </aside>

      <article className="reader-doc">
        <div className="doc-shell">
          <div className="doc-actions" aria-label="Report actions">
            <Link href="/knowledge"><BookOpen aria-hidden="true" />知识库</Link>
            <Link href={`/reports/${id}/trace`}><GitBranch aria-hidden="true" />决策链路</Link>
          </div>

          <header className="doc-hero">
            <span className="preview-pill">Report Mock · 示例研究档案</span>
            <h1>AI 协作写作与知识工作台竞品分析报告</h1>
            <div className="doc-meta" aria-label="报告元信息">
              <span className="doc-meta-card"><Users aria-hidden="true" /><strong>7</strong> 位专家</span>
              <span className="doc-meta-card"><FileText aria-hidden="true" /><strong>9</strong> 条示例证据</span>
              <span className="doc-meta-card"><Clock3 aria-hidden="true" /><strong>Mock</strong> 执行</span>
              <span className="doc-meta-card"><ShieldCheck aria-hidden="true" /><strong>QA</strong> pass with gaps</span>
            </div>
            <div className="stats-dashboard" aria-label="核心数据仪表盘">
              <article className="stat-card"><div className="stat-top"><FileText aria-hidden="true" /><strong>9</strong></div><span>Mock 证据条目</span></article>
              <article className="stat-card"><div className="stat-top"><Network aria-hidden="true" /><strong>3</strong></div><span>示例信源类型</span></article>
              <article className="stat-card"><div className="stat-top"><ShieldCheck aria-hidden="true" /><strong>86</strong></div><span>最高证据质量分</span></article>
              <article className="stat-card"><div className="stat-top"><TriangleAlert aria-hidden="true" /><strong>1</strong></div><span>需人工关注缺口</span></article>
            </div>
          </header>

          <section id="summary" className="doc-section">
            <h2>执行摘要</h2>
            <p><span className="highlight">Notion AI 更适合存量文档协作场景，而 Gamma 更偏向从零生成展示型内容。</span></p>
            <p>当前证据可以支持“产品入口和交付物形态差异明显”，但不能支持“某一方用户满意度显著领先”的强结论，因为公开用户反馈样本仍不足。</p>
            <ChapterFooter sources={["10", "24", "31"]} action="按批注深化本章" note="先在本章划线写批注，再进入后续重做流程" />
          </section>

          <section id="positioning" className="doc-section">
            <h2>产品定位</h2>
            <p>Notion AI 的优势集中在已有知识库、团队文档和项目上下文的连续协作；Gamma 则把价值前置到“从输入主题到可展示页面”的生成链路，更适合需要快速交付外部展示材料的轻量团队。</p>
            <p>飞书妙记更接近会议与沟通记录的生产力入口。判断它与 Notion AI、Gamma 是否构成直接竞争，需要结合用户的实际工作流，而不是只比较 AI 生成能力。</p>
            <ChapterFooter sources={["03", "15", "29"]} />
          </section>

          <section id="pricing" className="doc-section">
            <h2>定价策略</h2>
            <p>价格页证据显示，竞品普遍采用免费入口加团队升级的结构。强差异不在价格数字本身，而在套餐边界对协作人数、AI 用量与导出能力的限制。</p>
            <ChapterFooter sources={["08", "12", "27", "42"]} />
          </section>

          <section id="voice" className="doc-section">
            <h2>用户体验</h2>
            <p>公开反馈样本显示，用户对生成质量的评价常与具体使用场景绑定：演示生成用户更关注成稿速度和视觉稳定性，知识库用户更关注上下文理解、引用准确性和团队权限。</p>
            <p>当前样本不足以支持“用户满意度领先”的排序结论，因此本章只保留趋势性观察，并把需要补充授权访谈或规模化评论样本的位置标为数据缺口。</p>
            <ChapterFooter sources={["44", "45", "66"]} action="按批注深化本章" note="补充样本来源后，可重新生成用户体验判断" />
          </section>

          <section id="risk" className="doc-section">
            <h2>数据缺口与风险</h2>
            <p>缺少授权的后台使用数据、规模化用户访谈和近期留存指标，因此报告需要把“使用深度”和“长期付费意愿”标为待验证假设。</p>
            <ChapterFooter sources={["51", "66"]} action="补充批注后返工" note="当前缺口不会自动升级为强结论" />
          </section>
        </div>
      </article>

      <aside className="reader-inspector">
        <div className="inspector-tabs" role="tablist" aria-label="报告辅助工作区">
          <button className="inspector-tab"><BookMarked aria-hidden="true" />知识库 / 标注 (0)</button>
          <button className="inspector-tab active"><Link2 aria-hidden="true" />证据来源 ({mockEvidence.length})</button>
        </div>
        <div className="inspector-head"><span className="inspector-title">证据 / 批注</span><button className="inspector-filter"><SlidersHorizontal aria-hidden="true" />上下文</button></div>
        <div className="annotation-empty"><strong>我的批注 (0)</strong><span>划选正文后，可将亮点、存疑或补充判断沉淀为批注。</span></div>
        <div className="margin-note-list">
          {mockEvidence.slice(0, 2).map((evidence, index) => (
            <article key={evidence.id} className="margin-note">
              <span className={`source-badge ${index === 0 ? "official" : ""}`}>{index === 0 ? <BadgeCheck aria-hidden="true" /> : <Globe2 aria-hidden="true" />}{index === 0 ? "官方" : "Web"}</span>
              <div className="margin-note-head"><h4>{evidence.title}</h4><span className={evidence.level === "high" ? "chip sage" : "chip warn"}>{evidence.level === "high" ? "高置信" : "中置信"} {evidence.confidence}</span></div>
              <span className="margin-note-meta">{evidence.source}</span>
              <p>{evidence.summary}</p>
              <span className="evidence-link-tag">关联：{index === 0 ? "执行摘要" : "数据缺口"}</span>
              <div className="note-actions"><button className="note-action"><BookmarkPlus aria-hidden="true" />加入知识库</button><button className="note-action"><MessageSquare aria-hidden="true" />批注</button></div>
            </article>
          ))}
        </div>
      </aside>
    </section>
  );
}
