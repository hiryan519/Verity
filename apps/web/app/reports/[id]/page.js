import Link from "next/link";
import {
  BadgeCheck, BookMarked, BookOpen, BookmarkPlus, Clock3, FileText, GitBranch,
  Globe2, Link2, MessageSquare, Network, ShieldCheck, SlidersHorizontal, Sparkles, TriangleAlert, Users
} from "lucide-react";
import { getApiData } from "@/lib/api";
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
        <div className="source-pills">{sources.map((source) => <a key={source} href={`#evidence-${source}`} className="source-pill">[{source}]</a>)}</div>
      </div>
      {action ? <div className="chapter-action-row"><button className="chapter-action"><Sparkles aria-hidden="true" />{action}</button><span>{note}</span></div> : null}
    </div>
  );
}

function EvidenceInspector({ evidence = [], title = "证据 / 批注" }) {
  return (
    <aside className="reader-inspector">
      <div className="inspector-tabs" role="tablist" aria-label="报告辅助工作区">
        <button className="inspector-tab"><BookMarked aria-hidden="true" />知识库 / 标注 (0)</button>
        <button className="inspector-tab active"><Link2 aria-hidden="true" />证据来源 ({evidence.length})</button>
      </div>
      <div className="inspector-head"><span className="inspector-title">{title}</span><button className="inspector-filter"><SlidersHorizontal aria-hidden="true" />上下文</button></div>
      <div className="annotation-empty"><strong>我的批注 (0)</strong><span>真实批注入口将在知识库增强阶段接入；当前先保证证据和风险可追溯。</span></div>
      <div className="margin-note-list">
        {evidence.slice(0, 8).map((evidenceItem, index) => (
          <article key={evidenceItem.id} id={`evidence-${evidenceItem.id}`} className="margin-note">
            <span className={`source-badge ${evidenceItem.source_type === "official" ? "official" : ""}`}><Globe2 aria-hidden="true" />{evidenceItem.source_type === "official" ? "官方" : evidenceItem.platform || "Web"}</span>
            <div className="margin-note-head"><h4>{evidenceItem.title}</h4><span className={evidenceItem.confidence_level === "high" ? "chip sage" : "chip warn"}>{evidenceItem.confidence_level || "未分级"} {evidenceItem.confidence ?? "-"}</span></div>
            <span className="margin-note-meta">{evidenceItem.source_label || evidenceItem.url || "来源未记录"} · {evidenceItem.captured_at || "时间未记录"}</span>
            <p>{evidenceItem.summary}</p>
            {evidenceItem.risk_note ? <span className="evidence-risk">风险：{evidenceItem.risk_note}</span> : null}
            {evidenceItem.url ? <a className="evidence-link-tag" href={evidenceItem.url} target="_blank" rel="noreferrer">打开来源</a> : null}
          </article>
        ))}
      </div>
    </aside>
  );
}

function RealReportPage({ item, dataSource }) {
  const artifact = item.report_artifact;
  const payload = artifact.payload || {};
  const sections = Array.isArray(payload.sections) ? payload.sections : [];
  const evidence = item.evidence || [];
  const references = payload.claim_evidence_refs || [];
  const sourcesFor = (sectionId) => references.filter((reference) => reference.section_id === sectionId).flatMap((reference) => reference.evidence_ids || []);

  return (
    <section className="report-reader">
      <aside className="reader-toc">
        <span className="reader-toc-title">目录</span>
        <div className="progress-row" aria-label="阅读进度"><div className="reading-progress"><span /></div><span className="progress-value">12%</span></div>
        <nav aria-label="报告目录">{sections.map((section, index) => <a key={section.id || index} className={index === 0 ? "active" : ""} href={`#${section.id || `section-${index}`}`}><span className="toc-index">{String(index + 1).padStart(2, "0")}</span><span>{section.title || `章节 ${index + 1}`}</span></a>)}</nav>
      </aside>

      <article className="reader-doc">
        <div className="doc-shell">
          <div className="doc-actions" aria-label="Report actions"><Link href="/knowledge"><BookOpen aria-hidden="true" />知识库</Link><Link href={`/reports/${item.id}/trace`}><GitBranch aria-hidden="true" />决策链路</Link></div>
          <header className="doc-hero">
            <span className="preview-pill real-pill">真实报告 · {dataSource?.mode || "llm-report-writer"}</span>
            <h1>{item.title}</h1>
            <div className="doc-meta" aria-label="报告元信息"><span className="doc-meta-card"><Users aria-hidden="true" /><strong>{item.claim_count || 0}</strong> 个结论</span><span className="doc-meta-card"><FileText aria-hidden="true" /><strong>{evidence.length}</strong> 条 Evidence</span><span className="doc-meta-card"><Clock3 aria-hidden="true" /><strong>{item.updated_at || "-"}</strong></span><span className="doc-meta-card"><ShieldCheck aria-hidden="true" /><strong>QA</strong> {artifact.qa_verdict}</span></div>
            <div className="stats-dashboard" aria-label="核心数据仪表盘"><article className="stat-card"><div className="stat-top"><FileText aria-hidden="true" /><strong>{evidence.length}</strong></div><span>可复查 Evidence</span></article><article className="stat-card"><div className="stat-top"><Network aria-hidden="true" /><strong>{new Set(evidence.map((entry) => entry.source_type || entry.platform)).size}</strong></div><span>来源类型</span></article><article className="stat-card"><div className="stat-top"><ShieldCheck aria-hidden="true" /><strong>{Math.max(...evidence.map((entry) => entry.confidence || 0), 0)}</strong></div><span>最高证据质量分</span></article><article className="stat-card"><div className="stat-top"><TriangleAlert aria-hidden="true" /><strong>{(payload.risk_disclosures || []).length}</strong></div><span>风险披露</span></article></div>
          </header>

          {sections.map((section, index) => {
            const sectionId = section.id || `section-${index}`;
            const sourceIds = sourcesFor(sectionId);
            const paragraphs = String(section.content || "").split(/\n\s*\n/).filter(Boolean);
            return <section key={sectionId} id={sectionId} className="doc-section"><h2>{section.title || `章节 ${index + 1}`}</h2>{paragraphs.length ? paragraphs.map((paragraph, paragraphIndex) => <p key={paragraphIndex}>{paragraph}</p>) : <p>本章节暂无可交付内容。</p>}<ChapterFooter sources={sourceIds} /></section>;
          })}
          {payload.risk_disclosures?.length ? <section id="risk" className="doc-section"><h2>风险披露</h2>{payload.risk_disclosures.map((risk, index) => <p key={index}>{typeof risk === "string" ? risk : JSON.stringify(risk)}</p>)}</section> : null}
        </div>
      </article>

      <EvidenceInspector evidence={evidence} />
    </section>
  );
}

function ReworkReportPage({ item, dataSource }) {
  const evidence = item.evidence || [];
  const qa = item.qa_gate || {};
  return (
    <section className="report-reader">
      <aside className="reader-toc"><span className="reader-toc-title">研究状态</span><nav aria-label="研究状态"><a className="active" href="#qa-status"><span className="toc-index">01</span><span>QA 返工</span></a><a href="#evidence-status"><span className="toc-index">02</span><span>已采集证据</span></a></nav></aside>
      <article className="reader-doc"><div className="doc-shell"><div className="doc-actions"><Link href={`/reports/${item.id}/trace`}><GitBranch aria-hidden="true" />决策链路</Link></div><header className="doc-hero"><span className="preview-pill">研究结果 · {dataSource?.mode || item.data_source}</span><h1>{item.title}</h1><div className="doc-meta"><span className="doc-meta-card"><FileText aria-hidden="true" /><strong>{evidence.length}</strong> 条 Evidence</span><span className="doc-meta-card"><TriangleAlert aria-hidden="true" /><strong>QA</strong> rework</span></div></header><section id="qa-status" className="doc-section"><h2>报告暂未签发</h2><p>本次研究已经完成证据采集、专家分析和 QA 检查，但 Analysis Pack 尚未达到报告交付条件。系统没有调用 Report Writer，也没有把返工状态包装成最终报告。</p><div className="qa-issues">{(qa.issues || ["当前 Analysis Pack 需要返工"]).slice(0, 6).map((issue, index) => <p key={index}>{typeof issue === "string" ? issue : issue.description || JSON.stringify(issue)}</p>)}</div><ChapterFooter sources={[]} /></section><section id="evidence-status" className="doc-section"><h2>当前已取得的证据</h2><p>以下 Evidence 已保留来源、抓取时间、评分和风险，可用于后续返工或人工确认。</p></section></div></article><EvidenceInspector evidence={evidence} title="Evidence / QA 风险" /></section>
  );
}

export default async function ReportPage({ params }) {
  const { id } = await params;

  const { item, dataSource } = await getApiData(`/api/reports/${id}`);
  if (item && item.data_source !== "mock-seed") {
    if (item.report_artifact) return <RealReportPage item={item} dataSource={dataSource} />;
    return <ReworkReportPage item={item} dataSource={dataSource} />;
  }

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
