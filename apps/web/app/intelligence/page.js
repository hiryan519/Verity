import { SectionTitle } from "@/components/ui";

export default function IntelligencePage() {
  return (
    <div>
      <SectionTitle
        eyebrow="Competitive Intelligence"
        title="竞争情报中心"
        description="情报中心后续只能展示来自结构化数据和可复查证据的指标。当前为 P1 占位，不展示无法解释的夸大指标。"
        badge="P1 placeholder"
      />

      <div className="grid-3">
        {["报告概览", "信源结构", "专家贡献"].map((title) => (
          <article key={title} className="panel p-5">
            <h2 className="card-title">{title}</h2>
            <p className="mt-3 text-sm leading-6 text-black/60">等待 SQLite 结构化数据接入后展示。Mock 阶段不生成装饰性图表。</p>
          </article>
        ))}
      </div>
    </div>
  );
}
