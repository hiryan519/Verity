import Link from "next/link";
import { Calculator, Check, Lock, MessageSquare, Route, ShieldCheck, Split } from "lucide-react";

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
    confidence: "conf 91",
    content: "分析 AI 模型价格时，不能只比较订阅价；必须追问同等价格下 API 调用额度、token 单价和用量上限。",
    source: "用户批注",
    impact: "定价分析任务"
  },
  {
    id: "visual-memory-official-case-bias",
    name: "官方价格优先",
    confidence: "conf 88",
    content: "价格 Claim 默认优先绑定官网价格页；媒体或博客只能作为补充解释，不能替代价格源。",
    source: "QA 返工",
    impact: "证据绑定规则"
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

function StatusIcon({ status }) {
  return status === "allowed" ? <Check aria-hidden="true" /> : <Lock aria-hidden="true" />;
}

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
      <section className="expert-governance-frame">
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
                      <StatusIcon status={tool.status} />
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
                <span className="memory-tab active">Active Memory</span>
                <span className="memory-tab">Candidate</span>
              </div>
              <div className="memory-list">
                {visualMemories.map((memory) => (
                  <article key={memory.id} className="memory-item">
                    <div className="memory-item-head">
                      <strong>{memory.name}</strong>
                      <span className="memory-score">{memory.confidence}</span>
                    </div>
                    <p>{memory.content}</p>
                    <div className="memory-provenance">
                      <span>
                        {memory.source === "QA 返工" ? <ShieldCheck aria-hidden="true" /> : <MessageSquare aria-hidden="true" />}
                        来源：{memory.source}
                      </span>
                      <span>
                        <Route aria-hidden="true" />
                        影响：{memory.impact}
                      </span>
                    </div>
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
                    <strong>
                      {skill.id === "visual-skill-package-boundary" ? <Split aria-hidden="true" /> : <Calculator aria-hidden="true" />}
                      {skill.name} · {skill.version}
                    </strong>
                    <span>{skill.summary}</span>
                  </article>
                ))}
              </div>
            </section>
          </aside>
        </div>
      </section>
    </div>
  );
}
