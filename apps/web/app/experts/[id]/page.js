import Link from "next/link";

import { getApiData, toolStatusLabel } from "@/lib/api";

export const dynamic = "force-dynamic";

function safeJson(value) {
  return JSON.stringify(value, null, 2);
}

function statusClass(status) {
  return status === "allowed" ? "allowed" : "disabled";
}

const visualMemories = [
  {
    id: "visual-memory-token-pricing",
    name: "Token 维度比价",
    confidence: "82%",
    content: "比较 API 价格时必须换算同预算 token 可用量、调用次数和套餐限制。",
    source: "用户批注",
    impact: "定价分析任务"
  },
  {
    id: "visual-memory-official-case-bias",
    name: "官网案例偏差",
    confidence: "76%",
    content: "官网客户案例只能作为官方筛选样本，不能支撑自然用户体验结论。",
    source: "QA 返工",
    impact: "用户体验分析 / 证据绑定规则"
  }
];

const visualSkills = [
  {
    id: "visual-skill-package-boundary",
    name: "套餐边界拆解",
    version: "v1.2",
    summary: "当价格包含 seat、quota、API 调用额度时触发，用于生成可比性风险。"
  },
  {
    id: "visual-skill-unit-price",
    name: "单位价格归一",
    version: "v0.8",
    summary: "将订阅价、token、调用次数和团队席位拆成可对比维度。"
  }
];

export default async function ExpertDetailPage({ params }) {
  const { id } = await params;
  const { item: expert, error } = await getApiData(`/api/experts/${id}`);

  if (!expert) {
    return (
      <div className="expert-page-shell">
        <Link href="/experts" className="expert-button">返回专家公会</Link>
        <section className="panel p-6">
          <p className="eyebrow">Expert Detail</p>
          <h1 className="font-editorial text-3xl font-medium">专家不存在</h1>
          <p className="mt-3 text-sm text-[color:var(--muted)]">{error || "当前专家注册表未返回该专家。"}</p>
        </section>
      </div>
    );
  }

  return (
    <div className="expert-page-shell">
      <header className="expert-detail-head">
        <div className="expert-crumb">
          <Link href="/experts" className="expert-button">‹ 返回</Link>
          <span>专家公会</span>
          <span>/</span>
          <strong>{expert.name}</strong>
        </div>
      </header>

      <div className="expert-config-grid">
        <div className="expert-logic">
          <section className="config-block">
            <div className="config-title">
              <h2>专家行为规则</h2>
              <span>只读治理视图 · 底座 Prompt 不直接暴露</span>
            </div>
            <div className="code-panel">
              <pre>{`专家：${expert.name}
当前模型：默认模型
层级：${expert.layer}
定位：${expert.responsibility}

行为规则：
${expert.responsibilities.map((item) => `- ${item}`).join("\n")}

行为边界：
${expert.boundaries.map((item) => `- ${item}`).join("\n")}`}</pre>
            </div>
          </section>

          <section className="config-block">
            <div className="config-title">
              <h2>输出结构约束</h2>
              <span>只读 Schema 摘要 · 修改需工程校验</span>
            </div>
            <div className="code-panel">
              <pre>{safeJson(expert.output_contract)}</pre>
            </div>
          </section>

          <section className="config-block">
            <div className="config-title">
              <h2>工具权限清单</h2>
              <span>系统内置工具授权，不支持页面新增工具</span>
            </div>
            <div className="tool-list">
              {expert.tool_permissions.map((tool) => (
                <div key={tool.key} className="tool-row">
                  <div>
                    <strong>{tool.name}</strong>
                    <span>{tool.description}</span>
                  </div>
                  <span className={`permission-status ${statusClass(tool.status)}`}>
                    <span className="permission-icon">{tool.status === "allowed" ? "✓" : "▢"}</span>
                    {toolStatusLabel(tool.status)}
                  </span>
                </div>
              ))}
            </div>
          </section>
        </div>

        <aside className="expert-assets">
          <section className="config-block">
            <div className="config-title">
              <h2>Memory 治理视图</h2>
              <span>只展示来源、状态和影响</span>
            </div>
            <div className="memory-tabs">
              <span className="active">Active Memory</span>
              <span>Candidate</span>
            </div>
            <div className="memory-list">
              {visualMemories.map((memory) => (
                <article key={memory.id} className="memory-item">
                  <div className="memory-item-head">
                    <strong>{memory.name}</strong>
                    <span>{memory.confidence}</span>
                  </div>
                  <p>{memory.content}</p>
                  <small>来源：{memory.source} · 影响对象：{memory.impact}</small>
                </article>
              ))}
            </div>
          </section>

          <section className="config-block">
            <div className="config-title">
              <h2>挂载 Skill</h2>
              <span>能力摘要，不在此编辑源码</span>
            </div>
            <div className="memory-list">
              {visualSkills.map((skill) => (
                <article key={skill.id} className="skill-item">
                  <strong>{skill.name} · {skill.version}</strong>
                  <span>{skill.summary}</span>
                </article>
              ))}
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}
