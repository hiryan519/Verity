# Verity TODO

> 执行规则：严禁多任务并行。任何时候只能有一个 `in progress` 任务；完成并通过验收后，才能进入下一项。
>
> 状态标记：`[x]` 已完成；`[ ]` 待开始或进行中。任务下方的 `Status` 使用 `completed`、`in progress`、`planned`、`deferred` 进一步说明状态。
>
> 编号规则：`P0/P1/P2/P3/P4` 表示阶段任务，`B1/B2/B3/B4/B5` 表示主线任务。每个编号只有一个定义，不再用两个不同名称表示同一个任务。
>
> 开发前读取规则：
> - 每轮必须读取：`AGENTS.md`、本文件的当前任务段落、`docs/DECISION_LOG.md`，并根据任务读取 `docs/ARCHITECTURE.md`、`docs/MECHANISM.md` 或 `docs/DESIGN.md`。
> - 阶段规划或新增任务时：检查相关 PRD 和决策记录；如果产品决策缺失且会影响范围，标记为 `待确认`，不能自行补规则。
> - 具体开发时：只有涉及产品边界、能力取舍或用户可见行为时，读取相关 PRD 段落。
> - 只有涉及 UI、视觉、交互或文案层级时，读取 `docs/DESIGN.md` 和已确认的 UI Preview。
> - 不再整读已完成阶段；除非当前任务需要追溯历史决策。
>
> 变更控制：小需求可随当前任务修；大需求必须先同步产品机制 / 架构文档，再加入本清单，避免 MVP 失控。
>
> 回滚策略：如果代码写崩且无法轻易修复，先停下来说明问题；除非用户明确同意，不执行 `git reset --hard`、删除或覆盖用户未提交文件。
>
> 提交规则：每完成一个开发模块，必须测试主流程、加载中、为空、接口报错状态；测通后立刻提交，并在本清单更新对应状态。

## Current Phase

- Phase: B3.9 真实 Web Workflow 接入与报告阅读闭环
- Goal: 让用户从工作台输入研究目标，经 Human Gate 确认后创建真实在线 Run，在执行页查看真实 Evidence、专家结果、QA 和 Trace；QA 通过时读取真实报告资产，QA 返工时阻断报告签发。
- Status: in progress（代码实现已完成，真实网页点击验收尚未完成）
- Success criteria:
  - 用户可以从网页创建真实在线 Run，并看到真实 `run_id`、数据源和执行结果。
  - Evidence、专家输出、QA Gate、Report Artifact 和 Trace 在页面之间保持同一 Run 关联。
  - QA `rework` 不触发 Report Writer，也不显示虚假的“报告已完成”。
  - QA `pass` / `pass_with_risk` 时可以读取真实报告资产，并保留 Claim / Evidence 关联。

## Task Order

### [ ] B3.9：真实 Web Workflow 接入与报告阅读闭环

- Goal: 将已验证的在线研究链路接入真实 Web Console，形成“输入 → Human Gate → Run → QA → 报告 / 返工”的可操作闭环。
- Scope:
  - 工作台研究目标提交到 `POST /api/research/runs`。
  - 调研范围确认页保留竞品、维度、市场、用户、时间范围和用户 URL 的 Human Gate。
  - 执行页调用真实在线 Run，展示 Evidence、专家动作、QA 和 Trace，不使用 `mock-data` 冒充执行过程。
  - QA `pass` / `pass_with_risk` 自动进入 Report Writer；`rework` 展示问题、数据缺口和返工状态。
  - 报告阅读页读取 `report_artifact`；决策链路页优先读取真实 Trace，无真实 Trace 时才展示明确标识的 Mock fallback。
- Non-goals:
  - 不把当前 Tavily 公开网页能力包装成全网抓取或绕过反爬能力。
  - 不在本任务引入真实知识库检索、图表增强或 Evolva Workflow 深度接管。
  - 不把当前 QA 为 `rework` 的案例改写成通过案例。
- Required reading:
  - `AGENTS.md`
  - `docs/DECISION_LOG.md`
  - `docs/ARCHITECTURE.md` 的 Web Adapter、Research Run 和 Trace 段落
  - `docs/MECHANISM.md` 的 Evidence、QA Gate、Report Writer 和 Trace 段落
  - `docs/DESIGN.md` 的工作台、Human Gate、执行页、报告页和决策链路页段落
- Acceptance criteria:
  - [ ] 从 `/workspace` 输入目标可进入真实范围确认页并创建 Run。
  - [ ] 执行页显示实际 `run_id`、数据源状态、Evidence 数量、QA 结果和 Trace 状态。
  - [ ] 同一个 Run 的 Evidence、专家输出、QA、报告和 Trace 可相互定位。
  - [ ] QA `rework` 时报告入口显示“未签发 / 需返工”，不会调用 Report Writer。
  - [ ] QA `pass` / `pass_with_risk` 时报告页读取真实 `report_artifact`，不回退到静态 Mock 报告。
- Validation:
  - [x] `apps/web` 生产构建通过。
  - [x] `apps/api` 回归测试通过。
  - [x] `/api/llm/status` 和 `/api/tavily/status` 返回 provider 可用状态。
  - [x] 关键页面路由 Smoke Test 通过。
  - [ ] 启动本地 API 和 Web 双服务，手动点击完成一次真实在线 Run 路径验收。
- Product decisions:
  - 公开网页和用户主动提供 URL 是当前唯一允许的外部来源。
  - Evidence 不足或 QA 返工是产品可见结果，不为了展示效果强行生成最终报告。
  - Mock fallback 必须显式标识，不能与真实 Run 混用。
- Status: in progress（代码已完成；剩余唯一动作是本地双服务下的真实网页点击验收）。

### [ ] B4：知识库作为证据源增强

- Goal: 让用户知识库成为按需调用的证据来源，而不是常驻专家上下文或 Research Memory。
- Scope:
  - 实现知识库按研究范围和检索条件命中条目。
  - 将命中条目转化为 `source_type = user_knowledge` 的 Evidence，保留原始来源和反馈入口。
  - 在报告阅读页右侧证据栏展示知识库来源并支持定位。
  - 用户保留、删除或标记不合适的引用后，将反馈写入 Candidate trial，进入降权或隔离路径。
- Non-goals:
  - 不把知识库、证据库、历史报告直接等同于 Research Memory。
  - 不将全部知识库内容预加载给所有专家。
  - 不因用户引用一次就自动生成 Active Memory。
- Required reading:
  - `AGENTS.md`
  - `docs/DECISION_LOG.md`
  - `docs/ARCHITECTURE.md` 的 Knowledge、Evidence 和 Web Adapter 段落
  - `docs/MECHANISM.md` 的 Knowledge Base、Evidence、Memory Candidate 段落
- Acceptance criteria:
  - [ ] 知识库命中内容可以转化为 `user_knowledge` Evidence，并保留来源和时间。
  - [ ] Evidence 侧栏可以定位知识库来源，且与普通公开网页来源区分。
  - [ ] 用户负反馈可以影响对应 Candidate trial 的降权或隔离状态。
  - [ ] 知识库内容只有在研究范围匹配时进入 Evidence / Analysis Pack。
- Validation:
  - [ ] 检查知识库命中、无命中、重复命中和来源缺失状态。
  - [ ] 检查删除引用和“不合适”反馈是否写入 Candidate trial。
  - [ ] 运行后端回归测试和报告页引用定位 Smoke Test。
- Product decisions:
  - `user_knowledge` 是证据来源类型，不是 Memory 类型。
  - 用户反馈优先进入 Candidate，经过多次验证后才可能影响 Active Memory。
- Status: planned

### [ ] P4：报告阅读与数据表达增强

- Goal: 在真实报告资产和证据引用稳定后，增强报告的结构化数据表达、批注沉淀和竞争情报浏览体验。
- Scope:
  - 有数据表和 Evidence 来源支撑的雷达图、柱状图、环形图及 CSV 导出。
  - 正文选中、亮点 / 认同 / 存疑 / 待办标注、批注和知识库入口。
  - 基于报告、Claim、Evidence 的三层知识图谱。
  - 来自真实结构化数据的竞争情报中心指标、报告概览、信源结构和专家贡献统计。
- Non-goals:
  - 不生成没有数据表和证据来源的装饰性图表。
  - 不在 UI 中展示无法解释的夸大指标。
  - 不把批注、知识库和历史报告直接包装成 Active Memory。
- Required reading:
  - `AGENTS.md`
  - `docs/DECISION_LOG.md`
  - `docs/DESIGN.md` 的报告阅读、标注和竞争情报中心段落
  - `docs/MECHANISM.md` 的 Evidence、Claim、Memory 和 Trace 段落
- Acceptance criteria:
  - [ ] 每个图表都能展开对应数据表和 Evidence 来源。
  - [ ] 推断数据、缺失数据和低置信数据有显式标记。
  - [ ] 批注可以定位正文，并能进入知识库入口。
  - [ ] 图谱节点可查看详情，Evidence 节点可打开来源。
  - [ ] 竞争情报指标全部来自可追溯的结构化数据。
- Validation:
  - [ ] 检查有数据、无数据、数据不足和来源冲突状态。
  - [ ] 检查图表、表格、Evidence、Claim 的互相定位。
  - [ ] 运行前端构建、报告页回归和 CSV 导出检查。
- Product decisions:
  - P4 必须在 B3.9 网页路径验收后开始；不以视觉装饰代替真实研究闭环。
  - 图表是报告解释层，不得成为脱离 Evidence 的独立结论来源。
- Status: planned

### [ ] B5：端到端验证与产品复盘

- Goal: 用真实竞品研究课题验证 Verity 的证据治理、QA、Trace 和 Memory 是否实际发挥作用。
- Scope:
  - 跑通研究目标、Human Gate、公开网页 Evidence、专家执行、QA、报告和 Trace。
  - 记录耗时、Evidence 数量、信源数量、QA rework、Trace 步骤、数据缺口和 Memory 使用情况。
  - 至少记录 3 个可解释 bad case，并说明系统如何发现或修复。
  - 输出 Validation Report，必要时更新 `docs/DECISION_LOG.md`、`docs/MECHANISM.md` 和本 TODO。
- Non-goals:
  - 不把少量个人案例包装成统计学意义上的行业效果证明。
  - 不提前编造简历中的效率、覆盖率或质量提升数字。
  - 不用人工主观评价替代来源复核、规则校验和真实运行记录。
- Required reading:
  - `AGENTS.md`
  - `docs/DECISION_LOG.md`
  - `docs/MECHANISM.md` 的 Evidence、QA、Trace、Memory 和验证段落
  - `docs/ARCHITECTURE.md` 的真实边界和数据流段落
- Acceptance criteria:
  - [ ] 至少一份真实竞品研究报告可打开，且 Evidence、QA 和 Trace 齐全。
  - [ ] 至少 3 个 bad case 有输入、发现机制、处理结果和复盘结论。
  - [ ] 所有结果指标都能回到真实 Run 记录。
- Validation:
  - [ ] 保存每次 Run 的结构化结果和失败原因。
  - [ ] 对比 QA 前后、返工前后和 Memory 试用前后的可观察差异。
  - [ ] 完成产品复盘并更新相关决策文档。
- Product decisions:
  - B5 证明的是产品机制确实被使用和验证，不追求用个人项目制造虚假的大样本效果。
- Status: planned

## Deferred Backlog

### [ ] B1：Research Memory 治理增强

- Reason deferred: 当前已完成本地最小治理和专家 checklist 影响，但 B4 知识库反馈和 B5 真实案例尚未提供足够的 Candidate trial 数据；过早扩展会增加记忆污染风险。
- Revisit trigger: B4 / B5 完成后，已有可审计的 Candidate trial、用户负反馈和专家使用记录。
- Planned scope:
  - 增加 Candidate trial 审计，记录任务、专家、报告影响、用户反馈和 QA 结果。
  - 实现 Candidate 升级建议、Active Memory 过期 / 降权 / 回滚 / 归档和负反馈 quarantine。
  - 评估显式同步 Evolva MemoryStore，以及将已验证经验沉淀为版本化 Skill / checklist 文件。
  - 增加 Memory 管理页面。
- Status: deferred

### [ ] B2：Evolva Workflow 深度接入（真实 Agent Workflow 接入）

- Reason deferred: P3 已完成最小受控 Evolva Workflow wrapper，但 B3.9 的 Web 闭环可以先通过 Verity Adapter 工作；此时深度接入会扩大底层依赖和调试范围。
- Revisit trigger: B3.9 网页路径、B4 证据来源和 B5 端到端验证稳定后，需要将真实研究 Workflow 交给 Evolva WorkflowEngine 执行。
- Planned scope:
  - 修复 / 安装完整 Evolva runtime 依赖。
  - 将 Verity Research Orchestrator 生成的 workflow spec 接入 Evolva WorkflowEngine。
  - 将真实 Workflow output 写入 Evidence、Claim、Analysis Pack 和 Trace。
  - 用至少一次真实或半真实研究 Workflow Trace 替换 smoke / local evidence workflow。
- Completed subtask: `P3-T5 Evolva Workflow 最小受控接入` 已完成，边界为 `is_real_workflow=true`、`is_real_research=false`；这不代表 B2 整体完成。
- Acceptance criteria:
  - [ ] 至少一次真实 Workflow Run 可在决策链路页展示。
  - [ ] Workflow 结果能进入 Analysis Pack 和 QA Gate。
  - [ ] Mock seed、local-db、Evolva workflow、真实在线研究四种来源明确区分。
- Status: deferred

## Completed Summary

| Task | Completed At | Validation | Commit/Trace |
|---|---|---|---|
| P0：产品机制与技术边界确认 | 2026-07 前 | 机制文档、决策日志、评分 / QA / Memory 测试 | `docs/MECHANISM.md`、`docs/DECISION_LOG.md` |
| P1：Web Console Mock 页面与 UI Preview 迁移 | 2026-07-16 | 页面启动、主路由、视觉 Smoke Test | `docs/DESIGN.md`、`docs/verity-ui-design-preview.html` |
| P2：SQLite、Evidence Scoring、Analysis Pack、QA Gate | 2026-07 前 | 后端回归测试与 API 读取检查 | `apps/api/tests/` |
| P3-T1～P3-T4：Evolva 接入点、Trace、Expert wrapper、Memory 最小治理 | 2026-07 前 | wrapper / smoke trace / local-db 验证 | `docs/EVOLVA_INTEGRATION.md` |
| P3-T5：Evolva Workflow 最小受控接入 | 2026-07 前 | 本地版本化 Workflow 写入 Evidence、Claim、Analysis Pack、QA、Trace | `is_real_workflow=true`、`is_real_research=false` |
| B3.1～B3.2：Expert Registry 与只读 API | 2026-07 前 | API 测试通过 | `apps/api/verity_api/expert_registry.py` |
| B3.3～B3.6：系统模块契约、Execution Contract、并行规划、Memory / Skill Context | 2026-07 前 | 契约和 planner 测试通过 | `apps/api/verity_api/system_module_registry.py`、`expert_execution_contracts.py` |
| B3.7：Provider Adapter、Tavily Evidence、三专家在线链路 | 2026-07-18 | 在线 Run 写入 Trace / Analysis Pack / QA；真实结果为 `rework` | `01a4af0` |
| B3.8：Report Writer QA 门控与 Report Artifact | 2026-07-18 | `rework` 阻断 Report Writer；资产读取和单元测试通过 | `586b352` |
