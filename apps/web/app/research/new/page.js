"use client";

import Link from "next/link";
import { Sprout } from "lucide-react";
import { useState } from "react";

const competitorOptions = ["Notion AI", "飞书妙记", "Gamma", "语雀", "Canva AI", "Tome", "Craft"];
const dimensionOptions = ["核心场景", "定价策略", "用户体验", "SWOT", "数据缺口", "增长策略"];

function ChoiceGroup({ options, initial }) {
  const [selected, setSelected] = useState(initial);

  function toggle(option) {
    setSelected((current) => current.includes(option) ? current.filter((item) => item !== option) : [...current, option]);
  }

  return (
    <div className="tag-cloud">
      {options.map((option) => (
        <button key={option} type="button" className={`choice-tag ${selected.includes(option) ? "selected" : ""}`} onClick={() => toggle(option)}>
          {option}
        </button>
      ))}
    </div>
  );
}

export default function NewResearchPage() {
  return (
    <section className="gate-page">
      <div className="section-head">
        <div>
          <p className="eyebrow">Human Gate</p>
          <h2>调研范围确认</h2>
          <p>复杂配置后置到 Human Gate。首页只输入目标，这里确认产品、竞品、维度、市场、目标用户和时间范围。</p>
        </div>
      </div>

      <div className="gate-stack">
        <article className="gate-card gate-intro">
          <span className="gate-icon"><Sprout aria-hidden="true" /></span>
          <div>
            <h3>在开始前，请确认几个关键项</h3>
            <p>这能帮助专家队更精准地锁定调研范围。</p>
          </div>
        </article>

        <article className="gate-card">
          <div className="request-quote">你的需求：帮我调研 Notion、飞书和 Gamma 在 AI 协作写作场景下的产品策略、定价与用户体验差异。</div>
          <h3>意图与领域确认</h3>
          <p>我们识别到你要调研的所属领域是「AI 协作写作与知识工作台」。是否准确？</p>
          <div className="gate-actions">
            <button type="button" className="soft-button selected">准确，继续</button>
            <button type="button" className="soft-button">大致准确，需要补充</button>
            <button type="button" className="soft-button">不准确，我来修改</button>
          </div>
        </article>

        <article className="gate-card">
          <h3>竞品选择</h3>
          <p>为你自动发现了以下候选竞品，请勾选希望重点对比的对象（可多选）。</p>
          <ChoiceGroup options={competitorOptions} initial={["Notion AI", "飞书妙记", "Gamma"]} />
          <input className="gate-input" placeholder="补充其他想调研的竞品，回车添加" />
        </article>

        <article className="gate-card">
          <h3>分析维度与视角</h3>
          <p>确认专家队需要覆盖的分析维度，后续报告会围绕这些问题组织证据和结论。</p>
          <ChoiceGroup options={dimensionOptions} initial={["核心场景", "定价策略", "用户体验", "数据缺口"]} />
          <div className="gate-select-row">
            <div className="gate-select">
              <label htmlFor="perspective">报告视角</label>
              <select id="perspective" defaultValue="AI 产品经理">
                <option>AI 产品经理</option><option>增长负责人</option><option>创业团队 CEO</option>
              </select>
            </div>
            <div className="gate-select">
              <label htmlFor="time-range">时间范围</label>
              <select id="time-range" defaultValue="近一年">
                <option>近一年</option><option>近六个月</option><option>近三个月</option>
              </select>
            </div>
          </div>
        </article>

        <Link href="/research/mock-001/run" className="gate-submit">确认范围，开始调研 Agent</Link>
      </div>
    </section>
  );
}
