import Link from "next/link";
import { mockEvidence } from "@/lib/mock-data";
import { ConfidenceChip, Panel, SectionTitle } from "@/components/ui";

export default function ReportPage({ params }) {
  return (
    <div>
      <SectionTitle
        eyebrow="Interactive Report"
        title="AI 协作写作竞品分析报告"
        description="报告是可交互研究档案。正文结论紧跟证据锚点，右侧证据栏解释来源、可信度和风险。"
        badge="Report mock"
      />

      <div className="three-column">
        <Panel title="目录" meta="sections">
          {["执行摘要", "产品定位", "定价策略", "用户声音", "数据缺口"].map((item) => (
            <a key={item} className="block rounded-md px-3 py-2 text-sm text-black/65 hover:bg-[color:var(--sage-light)] hover:text-[color:var(--sage)]" href={`#${item}`}>
              {item}
            </a>
          ))}
        </Panel>

        <article className="panel p-8">
          <h2 id="执行摘要" className="font-editorial text-2xl font-medium leading-10">执行摘要</h2>
          <p className="body-copy">
            Notion AI 更适合存量文档协作场景，而 Gamma 更偏向从零生成展示型内容。
            <span className="citation mx-1">🔗 2条证据</span>
            <ConfidenceChip score={64} level="medium" />
          </p>
          <p className="body-copy">当前证据可以支持“产品入口和交付物形态差异明显”，但不能支持“某一方用户满意度显著领先”的强结论，因为用户声音样本仍不足。</p>

          <h3 id="定价策略" className="mt-8 font-editorial text-lg font-medium">定价策略</h3>
          <p className="body-copy">
            竞品普遍采用免费入口加团队升级的结构。强差异不在价格数字本身，而在套餐边界对协作人数、AI 用量与导出能力的限制。
            <span className="citation mx-1">🔗 3条证据</span>
            <ConfidenceChip score={86} level="high" />
          </p>

          <div className="mt-6 rounded-xl border border-[color:var(--line)] bg-[color:var(--workspace)] p-4">
            <h3 className="text-sm font-semibold">QA 摘要</h3>
            <p className="mt-2 text-sm leading-6 text-black/60">Mock QA：证据充分性通过；用户声音维度存在数据缺口，报告中已降级为待验证假设。</p>
          </div>
        </article>

        <Panel title="证据 / 标注 / 知识库" meta="context">
          <div className="grid gap-3">
            {mockEvidence.map((evidence) => (
              <article key={evidence.id} className="panel p-4">
                <div className="mb-3 flex items-start justify-between gap-3">
                  <div>
                    <h3 className="text-sm font-semibold">{evidence.title}</h3>
                    <span className="text-xs text-[color:var(--muted)]">{evidence.source}</span>
                  </div>
                  <ConfidenceChip score={evidence.confidence} level={evidence.level === "high" ? "high" : "medium"} />
                </div>
                <p className="body-copy m-0 text-sm">{evidence.summary}</p>
              </article>
            ))}
          </div>
        </Panel>
      </div>

      <div className="mt-5 flex justify-end">
        <Link href={`/reports/${params.id}/trace`} className="btn btn-secondary">查看决策链路</Link>
      </div>
    </div>
  );
}
