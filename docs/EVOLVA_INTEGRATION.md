# Verity / Evolva Integration Notes

本文档记录 Verity Phase 3 对 Evolva 真实源码接入点的调研与最小接入方案。

## 1. 接入原则

- 不修改 Evolva 底层核心逻辑。
- Verity 通过 FastAPI Adapter / wrapper 读取或调用 Evolva 能力。
- Evolva 原始日志不直接展示给用户，必须映射为 Verity 的产品侧 `trace_steps`。
- Trace 展示前必须脱敏 API Key、Token、Cookie、Authorization 等敏感信息。
- Mock / local-db / evolva-adapter 三类数据源必须显式区分。

## 2. 已确认源码接入点

### 2.1 Workflow

源码：`evolva/workflow/engine.py`

可复用能力：

- `WorkflowEngine.run(spec)` 可执行 workflow spec。
- 支持 `tool`、`role`、`agent` 三类节点。
- 支持 `depends_on` 和拓扑排序。
- workflow run 会持久化到 `config.workflows_dir / "runs"`。

Verity 接入方式：

- 后续通过 wrapper 生成竞品研究 workflow spec。
- 无依赖的只读专家任务可以映射为无依赖节点。
- 依赖 Evidence Pack / Analysis Pack 的任务应通过 `depends_on` 顺序执行。

当前边界：

- 不能直接把 workflow logs 当用户可读 Trace。
- 需要把 workflow node output 转换为 Evidence / Claim / Analysis Pack。

### 2.2 Loop

源码：`evolva/loops/runner.py`

可复用能力：

- `LoopRunner.run()` 支持阶段化 loop、gate、resume、trace。
- loop phase 会写入 Evolva tracer。
- gate 思路可用于 Verity 的 QA Gate 解释。

Verity 接入方式：

- 暂不把 Verity 主流程直接改造成 Evolva Loop。
- 先复用其“阶段 + gate + trace”的结构思想。
- 后续如需真实 loop，可把 Research Orchestrator 的阶段映射为 loop phases。

### 2.3 Trace

源码：`evolva/agent/tracing.py`

可复用能力：

- `TraceRecorder.start() / event() / end()` 可生成结构化 trace run。
- trace run 包含 `run_id`、`status`、`user_input`、`final_answer`、`events`、`summary`。
- `TraceRecorder.list_runs()`、`load()`、`timeline()` 可读取历史 trace。
- Evolva TraceRecorder 内置 Redactor，会对敏感字段和值做脱敏。

Verity 接入方式：

- 新增 `EvolvaAdapter.trace_to_verity_steps()`。
- 将 Evolva event 映射为 Verity `trace_steps`：
  - `run_meta` -> 需求理解。
  - `task_route` -> 编排派遣。
  - `multi_agent_auto_route` -> 专家协作。
  - `policy_decision` -> 工具边界。
  - `tool_call` / `tool_error` -> 工具调用。
  - `loop_phase` -> 阶段执行。
- Verity 页面只展示映射后的 PM 可读 Trace，不直接倾倒原始 JSON。

当前已实现：

- `/api/evolva/traces`
- `/api/evolva/traces/{run_id}/verity-steps`
- `/api/evolva/smoke-trace`

### 2.4 Memory

源码：`evolva/agent/memory.py`

可复用能力：

- `MemoryStore.add()` 支持 kind、content、confidence、source、evidence、status。
- `MemoryStore.context()` 只召回 active memory。
- 支持 `draft`、`quarantined`、`rolled_back` 等治理状态。

Verity 接入方式：

- Verity 自己先维护 `research_memories` 表。
- 只有满足 `docs/MECHANISM.md` active 条件的内容，后续才考虑写入 Evolva active memory。
- 低可信、冲突、过期、不可复查内容只允许成为 candidate 或 quarantined。

### 2.5 Skills

源码：`evolva/agent/skills.py`

可复用能力：

- `SkillStore.list()`、`match()`、`context()`、`upsert()`。
- Skill 有 status 和 metadata。

Verity 接入方式：

- Skill 不是专家本体。
- Skill 作为 Expert Agent 可调用的方法、知识、Prompt 片段或 checklist。
- 专家 Agent 仍应保留独立目标、状态、工具边界、结构化输出和 Trace。

### 2.6 Multi-Agent

源码：`evolva/agent/multi_agent.py`

可复用能力：

- `AgentRole`
- `TaskRouter`
- `MultiAgentCoordinator`
- `delegate_report()` / `collaborate_report()`

当前边界：

- Evolva 默认角色是 planner / researcher / coder / reviewer，不等同于 Verity 专家。
- Verity 需要把 Research Orchestrator、Evidence Collector、Product Analyst、QA Agent 等映射为独立 Expert Agent。
- 源码中的 `collaborate_report()` 当前按角色顺序执行；Verity 的“无依赖只读任务并行”需要在 Adapter 层补 wrapper，或后续扩展 Evolva runtime。

P3.3 最小实现：

- Verity 不直接暴露 Evolva 默认角色作为产品专家。
- 新增 `apps/api/verity_api/verity_experts.py`，在 Adapter 层定义 Verity 专家：
  - Research Orchestrator
  - Evidence Collector
  - Product Analyst
  - Business / Pricing Analyst
  - Cross-validation Agent
  - QA Agent
  - Report Writer Agent
- `coder` 不进入 Verity 竞品研究主链路。
- `evidence_collector`、`product_analyst`、`business_pricing_analyst` 被标记为无依赖只读任务，可并行执行。
- 当前实现是 deterministic local-db wrapper，用于验证专家选择、并行执行、结构化输出、Analysis Pack 汇总和 QA Gate，不等同于真实在线研究。

已实现 API：

- `GET /api/verity/experts`
- `POST /api/verity/experts/run-minimal`

## 3. 当前环境限制

当前本地 Python 环境缺少 `langgraph`，导致完整 `EvolvaAgent` 实例化会失败。

因此 P3 最小接入采用降级策略：

- Trace / Memory / Skills 直接使用对应 Store / Recorder。
- 完整 EvolvaAgent / ToolRegistry / LangGraph runtime 不作为 API 启动的硬依赖。
- `/api/evolva/status` 会返回 `dependency_warnings`，而不是让 Verity API 崩溃。

这属于技术依赖问题，不是产品决策问题。

## 4. 已实现 Adapter

源码：`apps/api/verity_api/evolva_adapter.py`

能力：

- `status()`：读取 Evolva runtime 状态。
- `list_traces()`：列出 Evolva trace runs。
- `load_trace()`：读取并脱敏 trace。
- `trace_to_verity_steps()`：将 Evolva trace event 映射为 Verity trace step。
- `create_smoke_trace()`：生成只读 smoke trace，用于验证映射链路。

## 5. 下一步

1. 安装或修复 Evolva 完整 runtime 依赖后，验证 `EvolvaAgent` 和 `WorkflowEngine` 真实执行。
2. 将 Research Orchestrator 生成的 workflow spec 交给 Evolva WorkflowEngine。
3. 将真实 workflow trace 映射并写入 `trace_steps`。
4. 在 Adapter 层实现 Verity Expert Agent 并行 wrapper。
5. 将通过治理规则的 Research Memory candidate 影响下一次专家选择或报告风格。
