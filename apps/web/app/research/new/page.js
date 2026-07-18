"use client";

import { ArrowRight, Link2, Sprout } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { postApiData } from "@/lib/api";

const competitorOptions = ["滴滴出行", "曹操出行", "Notion AI", "飞书妙记", "Gamma", "语雀", "Canva AI", "Tome"];
const dimensionOptions = ["产品定位", "核心场景", "定价策略", "用户体验", "增长策略", "数据缺口"];

function ChoiceGroup({ options, selected, onToggle }) {
  return (
    <div className="tag-cloud">
      {options.map((option) => (
        <button key={option} type="button" className={`choice-tag ${selected.includes(option) ? "selected" : ""}`} onClick={() => onToggle(option)}>
          {option}
        </button>
      ))}
    </div>
  );
}

export default function NewResearchPage() {
  const router = useRouter();
  const [goal, setGoal] = useState("");
  const [competitors, setCompetitors] = useState(["Notion AI", "飞书妙记", "Gamma"]);
  const [dimensions, setDimensions] = useState(["产品定位", "定价策略", "用户体验"]);
  const [market, setMarket] = useState("中国出行市场");
  const [audience, setAudience] = useState("产品经理");
  const [timeRange, setTimeRange] = useState("近三年");
  const [userUrls, setUserUrls] = useState("");
  const [extraCompetitor, setExtraCompetitor] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const value = new URLSearchParams(window.location.search).get("goal") || "";
    setGoal(value);
    if (value.includes("滴滴") || value.includes("曹操")) setCompetitors(["滴滴出行", "曹操出行"]);
  }, []);

  function toggleValue(value, setter) {
    setter((current) => current.includes(value) ? current.filter((item) => item !== value) : [...current, value]);
  }

  function addCompetitor(event) {
    if (event.key !== "Enter") return;
    event.preventDefault();
    const value = extraCompetitor.trim();
    if (value && !competitors.includes(value)) setCompetitors((current) => [...current, value]);
    setExtraCompetitor("");
  }

  async function submitResearch(event) {
    event.preventDefault();
    if (!goal.trim()) return setError("请先填写调研目标。");
    if (!competitors.length) return setError("至少选择一个竞品。");
    if (!dimensions.length) return setError("至少选择一个分析维度。");

    setSubmitting(true);
    setError("");
    const response = await postApiData("/api/research/runs", {
      research_goal: goal.trim(),
      competitors,
      dimensions,
      market,
      audience,
      time_range: timeRange
    });
    setSubmitting(false);
    if (response.error || !response.item?.id) {
      setError(response.error || "无法创建研究 Run，请确认 API 服务已启动。");
      return;
    }

    const urls = userUrls.split(/\r?\n|,/).map((url) => url.trim()).filter(Boolean);
    const query = new URLSearchParams({ auto: "1" });
    if (urls.length) query.set("urls", urls.join(","));
    router.push(`/research/${response.item.id}/run?${query.toString()}`);
  }

  return (
    <section className="gate-page">
      <div className="section-head">
        <div>
          <p className="eyebrow">Human Gate</p>
          <h2>调研范围确认</h2>
          <p>确认后才会创建真实研究 Run。公开网页由 Tavily 采集，用户 URL 会作为补充来源；无法取得的数据会保留为数据缺口。</p>
        </div>
      </div>

      <form className="gate-stack" onSubmit={submitResearch}>
        <article className="gate-card gate-intro">
          <span className="gate-icon"><Sprout aria-hidden="true" /></span>
          <div>
            <h3>在开始前，请确认几个关键项</h3>
            <p>范围确认会影响专家选择、检索查询和最终报告结构。</p>
          </div>
        </article>

        <article className="gate-card">
          <div className="request-quote">你的需求</div>
          <textarea className="gate-textarea" value={goal} onChange={(event) => setGoal(event.target.value)} placeholder="例如：分析滴滴出行和曹操出行近几年的发展趋势。" />
        </article>

        <article className="gate-card">
          <h3>竞品选择</h3>
          <p>选择本次研究需要重点比较的对象，也可以回车添加其他竞品。</p>
          <ChoiceGroup options={competitorOptions} selected={competitors} onToggle={(value) => toggleValue(value, setCompetitors)} />
          <input className="gate-input" value={extraCompetitor} onChange={(event) => setExtraCompetitor(event.target.value)} onKeyDown={addCompetitor} placeholder="补充其他竞品，回车添加" />
        </article>

        <article className="gate-card">
          <h3>分析维度与视角</h3>
          <p>只派出能服务于已确认维度的专家，不会为了展示多 Agent 而全员启动。</p>
          <ChoiceGroup options={dimensionOptions} selected={dimensions} onToggle={(value) => toggleValue(value, setDimensions)} />
          <div className="gate-select-row">
            <div className="gate-select"><label htmlFor="market">目标市场</label><input id="market" className="gate-control" value={market} onChange={(event) => setMarket(event.target.value)} /></div>
            <div className="gate-select"><label htmlFor="audience">目标用户</label><input id="audience" className="gate-control" value={audience} onChange={(event) => setAudience(event.target.value)} /></div>
            <div className="gate-select"><label htmlFor="time-range">时间范围</label><select id="time-range" value={timeRange} onChange={(event) => setTimeRange(event.target.value)}><option>近三年</option><option>近一年</option><option>近六个月</option><option>近三个月</option></select></div>
          </div>
        </article>

        <article className="gate-card">
          <div className="gate-card-heading"><div><h3>用户主动提供的 URL（可选）</h3><p>每行一个。系统只读取你主动提供的公开链接，不绕过登录或反爬。</p></div><Link2 aria-hidden="true" /></div>
          <textarea className="gate-textarea gate-url-input" value={userUrls} onChange={(event) => setUserUrls(event.target.value)} placeholder="https://example.com/product/pricing" />
        </article>

        {error ? <p className="form-error" role="alert">{error}</p> : null}
        <button type="submit" className="gate-submit" disabled={submitting}>{submitting ? "正在创建研究 Run…" : <><span>确认范围，开始真实调研</span><ArrowRight aria-hidden="true" /></>}</button>
      </form>
    </section>
  );
}
