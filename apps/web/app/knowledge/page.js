import { BookMarked, MessageSquareText, Search } from "lucide-react";

export default function KnowledgePage() {
  return (
    <section className="asset-page route-section">
      <div className="section-head">
        <div>
          <p className="eyebrow">Knowledge Base</p>
          <h2>知识库</h2>
          <p>保存用户主动收藏、标注和批注的研究资产。知识库不是 Research Memory，也不会默认改变后续 Agent 行为。</p>
        </div>
        <span className="preview-pill">P1 占位 · 未接入检索</span>
      </div>

      <div className="asset-toolbar">
        <label><Search aria-hidden="true" /><input aria-label="搜索知识资产" placeholder="搜索标题、来源或批注" disabled /></label>
        <button disabled>全部资产</button>
      </div>

      <div className="asset-empty">
        <span className="asset-empty-icon"><BookMarked aria-hidden="true" /></span>
        <h3>知识资产将在这里汇总</h3>
        <p>后续从报告中保存的证据、段落与批注会进入这里，并保留来源与关联报告。当前尚未实现真实知识库检索。</p>
        <span className="asset-empty-note"><MessageSquareText aria-hidden="true" />加入知识库不会自动写入 Active Memory</span>
      </div>
    </section>
  );
}
