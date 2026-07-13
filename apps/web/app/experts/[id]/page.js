import Link from "next/link";

import { getApiData, toolStatusLabel } from "@/lib/api";

export const dynamic = "force-dynamic";

function safeJson(value) {
  return JSON.stringify(value, null, 2);
}

function statusClass(status) {
  return status === "allowed" ? "allowed" : "disabled";
}

export default async function ExpertDetailPage({ params }) {
  const { id } = await params;
  const [{ item: expert, error }, { item: runtimeContext }] = await Promise.all([
    getApiData(`/api/experts/${id}`),
    getApiData(`/api/experts/${id}/runtime-context`)
  ]);

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

  const activeMemories = runtimeContext?.checklist_context || [];
  const candidateHints = runtimeContext?.trial_hints || [];
  const mountedSkills = runtimeContext?.mounted_skills || [];

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
              {[...activeMemories, ...candidateHints].length ? (
                <>
                  {activeMemories.map((memory) => (
                    <article key={memory.memory_id} className="memory-item">
                      <div className="memory-item-head">
                        <strong>Active · {memory.effect_strategy}</strong>
                        <span>Not Evidence</span>
                      </div>
                      <p>{memory.content}</p>
                      <small>来源：{memory.source_type || "unknown"}</small>
                    </article>
                  ))}
                  {candidateHints.map((memory) => (
                    <article key={memory.memory_id} className="memory-item">
                      <div className="memory-item-head">
                        <strong>Candidate · 试用提示</strong>
                        <span>低权重</span>
                      </div>
                      <p>{memory.content}</p>
                      <small>{memory.risk_note}</small>
                    </article>
                  ))}
                </>
              ) : (
                <article className="empty-governance">
                  <strong>暂无运行记忆</strong>
                  <span>当前专家没有可展示的 active memory 或 candidate trial hint。</span>
                </article>
              )}
            </div>
          </section>

          <section className="config-block">
            <div className="config-title">
              <h2>挂载 Skill</h2>
              <span>能力摘要，不在此编辑源码</span>
            </div>
            <div className="memory-list">
              {mountedSkills.length ? (
                mountedSkills.map((skill) => (
                  <article key={skill.skill_id} className="skill-item">
                    <strong>{skill.name} · {skill.version}</strong>
                    <span>{skill.summary}</span>
                  </article>
                ))
              ) : (
                <article className="empty-governance">
                  <strong>暂无挂载 Skill</strong>
                  <span>P0 只展示经治理的挂载关系，当前未配置版本化 Skill。</span>
                </article>
              )}
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}
