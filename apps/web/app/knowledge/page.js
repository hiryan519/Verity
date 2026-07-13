import { SectionTitle } from "@/components/ui";

export default function KnowledgePage() {
  return (
    <div>
      <SectionTitle
        eyebrow="Knowledge Base"
        title="知识库"
        description="知识库保存用户主动收藏、标注和批注的内容资产。它不是 Research Memory，也不会默认影响后续 Agent。"
        badge="P1 placeholder"
      />

      <div className="panel p-6">
        <h2 className="card-title">知识资产占位</h2>
        <p className="mt-3 text-sm leading-6 text-black/60">后续 P1 将支持报告段落标注、批注、加入知识库和检索。当前页面只建立路由和信息边界。</p>
      </div>
    </div>
  );
}
