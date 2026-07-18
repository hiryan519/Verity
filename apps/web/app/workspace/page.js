"use client";

import Link from "next/link";
import { ArrowUp, BadgeDollarSign, MessagesSquare, NotebookTabs, Presentation } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

const examples = [
  { Icon: NotebookTabs, title: "AI 笔记产品竞品分析", body: "比较目标用户、核心场景、价格层级和用户口碑。", goal: "比较 Notion AI、飞书妙记和 Gamma 在 AI 协作写作场景下的产品定位、定价和用户体验。" },
  { Icon: BadgeDollarSign, title: "B2B SaaS 定价策略", body: "拆解套餐边界、免费额度、团队版卖点和证据缺口。", goal: "分析 Linear、Jira 和 Asana 的 B2B SaaS 定价策略与套餐边界。" },
  { Icon: Presentation, title: "生成式演示工具定位", body: "比较 Gamma、Tome、Canva AI 在交付链路中的差异。", goal: "比较 Gamma、Tome 和 Canva AI 在生成式演示工具市场的产品定位。" },
  { Icon: MessagesSquare, title: "用户体验与机会点", body: "汇总公开反馈，标记高频痛点、冲突证据和数据缺口。", goal: "分析目标竞品公开用户体验反馈，识别高频痛点、冲突证据和数据缺口。" }
];

export default function WorkspacePage() {
  const router = useRouter();
  const [goal, setGoal] = useState("");

  function startResearch(event) {
    event.preventDefault();
    const value = goal.trim();
    if (value) router.push(`/research/new?goal=${encodeURIComponent(value)}`);
    else router.push("/research/new");
  }

  function useExample(exampleGoal) {
    router.push(`/research/new?goal=${encodeURIComponent(exampleGoal)}`);
  }

  return (
    <section className="hero">
      <div className="hero-shell">
        <h1>下午好，林研究员</h1>
        <p className="hero-copy">你的 AI 竞品分析 Agent —— 多领域专家协作，无证据不立论</p>

        <form className="prompt-card" onSubmit={startResearch}>
          <textarea
            aria-label="Research goal"
            value={goal}
            onChange={(event) => setGoal(event.target.value)}
            placeholder="想分析哪个市场、公司或竞争策略？例如：比较滴滴和曹操出行近几年的发展趋势。"
          />
          <div className="prompt-actions">
            <div className="composer-meta">
              <span className="chip sage">任务编排 Agent</span>
              <span>先进入调研范围确认</span>
            </div>
            <button type="submit" className="composer-submit" aria-label="提交调研目标">
              <ArrowUp aria-hidden="true" />
            </button>
          </div>
        </form>

        <p className="sample-title">试试这些示例</p>
        <div className="example-grid">
          {examples.map(({ Icon, title, body, goal: exampleGoal }) => (
            <button key={title} type="button" className="example-card" onClick={() => useExample(exampleGoal)}>
              <span className="sample-icon"><Icon aria-hidden="true" /></span>
              <strong>{title}</strong>
              <p>{body}</p>
            </button>
          ))}
        </div>

        <Link href="/experts" className="expert-strip">
          <div className="avatar-stack" aria-label="Expert Agent group">
            {[
              ["编", "研究编排专家"], ["证", "证据采集专家"], ["产", "产品分析专家"], ["价", "定价策略专家"],
              ["验", "交叉验证专家"], ["体", "用户体验分析专家"], ["QA", "QA 质检专家"], ["撰", "报告撰写专家"]
            ].map(([short, name]) => <span key={name} className="stack-avatar" title={name}>{short}</span>)}
          </div>
          <span>查看全部专家</span>
        </Link>
      </div>
    </section>
  );
}
