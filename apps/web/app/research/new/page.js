import Link from "next/link";
import { mockScope } from "@/lib/mock-data";
import { SectionTitle } from "@/components/ui";

const fields = [
  ["产品 / 领域", mockScope.domain],
  ["竞品", mockScope.competitors.join("、")],
  ["分析维度", mockScope.dimensions.join("、")],
  ["报告视角", mockScope.perspective],
  ["市场 / 用户", `${mockScope.market}；${mockScope.audience}`],
  ["时间范围", mockScope.timeRange]
];

export default function NewResearchPage() {
  return (
    <div>
      <SectionTitle
        eyebrow="Human Gate"
        title="调研范围确认"
        description="复杂配置放在执行前确认。这里展示 Agent 对输入目标的识别结果，用户确认后才进入调研执行页。"
        badge="Scope mock"
      />

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
        {fields.map(([label, value]) => (
          <div key={label} className="panel p-4">
            <span className="text-xs text-[color:var(--muted)]">{label}</span>
            <strong className="mt-2 block font-editorial text-[15px] font-medium leading-7">{value}</strong>
          </div>
        ))}
      </div>

      <div className="mt-5 flex justify-end gap-3">
        <Link href="/workspace" className="btn btn-secondary">返回工作台</Link>
        <Link href="/research/mock-001/run" className="btn btn-primary">开始 Mock 调研</Link>
      </div>
    </div>
  );
}
