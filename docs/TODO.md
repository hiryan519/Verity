# AI Product Research Agent Console TODO

版本：v0.1  
状态：P3.4 最小实现已完成，B3.1-B3.7 在线研究链路已完成；已实现真实 LLM 调用、模型路由、结构化输出校验、Trace、Tavily 公开网页 Evidence、独立在线 Run、三专家 Workflow、交叉验证受控重试和 QA Gate；在线案例已完成至 QA，但 QA 仍可能返回 rework，最终报告撰写与交付验证进入下一阶段；P1 主链路页面已按 UI Preview 完成视觉迁移
关联文档：`docs/AI_Product_Research_Agent_PRD.md`、`docs/ARCHITECTURE.md`、`docs/DECISION_LOG.md`、`docs/MECHANISM.md`、`docs/DESIGN.md`

## 文档分工

本文件是后续开发的一线入口，定位为“开发作战手册”，不替代机制文档和决策日志。

- `docs/TODO.md`：记录当前架构判断、阶段目标、任务顺序、关键产品决策摘要、已完成边界、延后事项和验收标准。后续开发优先从本文档定位下一步。
- `docs/MECHANISM.md`：记录面向产品机制理解和面试复盘的详细规则，例如证据可信度评分、QA Gate、Research Memory 治理。不要求每个开发任务都全文阅读，除非任务涉及对应机制。
- `docs/DECISION_LOG.md`：记录已经确认的重要产品 / 架构 / 范围决策及其原因，是判断冲突时的决策索引。
- `docs/ARCHITECTURE.md`：记录技术架构、模块边界和 Evolva 接入方案。
- `docs/DESIGN.md`：记录 UI 视觉规范。涉及页面、交互、视觉、排版时必须读取。

## 当前架构判断

Verity 采用“Evolva Agent Infra + Verity Web Adapter / Business Layer”的方式推进：

- 保留 Evolva 作为底层 Agent Infra 和学习对象，不为了单个页面深改 Evolva 内核。
- Verity 自己补充竞品研究业务层、证据治理、Analysis Pack、QA Gate、Trace 展示、Research Memory 治理和 Web Console。
- 当前前端采用 `apps/web` Next.js；后端采用 `apps/api` FastAPI；本地结构化数据采用 SQLite。
- 当前已完成 P1 Mock UI、P2 结构化数据与业务机制、P3 Evolva 接入的最小 wrapper。
- 当前真实程度边界：页面形态、SQLite local-db、Evidence Scoring、Analysis Pack、QA Gate、TraceRecorder 映射、Expert wrapper、Memory 最小治理已实现；真实 LLM expert execution 已可在本地或 Tavily Extract Evidence 上运行并写入 Trace / Analysis Pack / QA Gate；在线 Run 已保存研究范围、批量查询、Evidence provenance、content_hash 和专家链路。最终 Report Writer 在线交付、真实知识库检索和端到端报告质量验证仍待完成。
- 2026-07-13 已在 `docs/MECHANISM.md` 确认专家体系、Evidence Router / Evidence Slice、QA Brief Builder、Report Renderer、按需多实例和各专家执行契约；这些契约已落成 Expert Registry 与 Execution Contract，后续开发应继续沿用注册表和契约，不直接编写散落的 prompt。

## 0. 执行原则

- 先形态，后真实，再机制增强。
- 先完成 P0 主链路，再做高级体验。
- 每个任务必须有可验证结果。
- 不为了炫技扩大范围。
- 不绕过反爬，不伪造真实采集能力。
- 产品决策未定时，先标 `待确认`，不要在代码里偷做决定。
- TODO 中的“状态”必须同时说明已完成能力和未完成边界，避免把 mock / wrapper 误读为真实能力。
- 机制细节以 `docs/MECHANISM.md` 为准；TODO 只保留开发必须知道的摘要和链接。

## B3.7 已完成：在线 Evidence 接入与端到端验证

本任务已将 Tavily 成功提取的 Evidence 接入现有三专家 Workflow，并完成一次可追溯的在线案例运行。2026-07-18 的曹操出行验证 Run 真实提取 3 条 Evidence，调用产品分析、定价策略、用户体验三类专家，完成交叉验证和 QA；QA 结果为 `rework`，因此未把它包装成已通过的最终报告。

执行顺序：

1. 创建一次独立的在线研究 Run，保存研究目标、时间范围、分析维度和运行 ID。
2. 按分析维度生成多组公开网页查询，将 Tavily Extract 成功结果写入该 Run 的 Evidence Store；Search 摘要不得直接进入 Evidence。
3. 用至少 3 类真实专家读取这些 Evidence，结果写入 Trace、Analysis Pack 和 QA Gate；数据不足时保留 `data_gap`。
4. 修复交叉验证输出失败或触发一次受控重试；QA 只能输出通过、带风险通过或返工。
5. 完成一次在线案例后，再把该 Run 标记为 `is_real_research=true`；在此之前不得把 Tavily 采集适配包装成完整在线研究能力。已完成。

本任务完成标准：同一个 Run 中能看到 Evidence → 三类专家输出 → 交叉验证 → QA Gate 的完整关联，且每条 Evidence 保留 URL、抓取时间、评分、风险和 `content_hash`。已完成；QA 不通过时保留 `rework` 状态，不生成虚假的通过结论。

建议影响文件：

- `apps/api/verity_api/`：连接 Tavily Evidence Collection、在线 Run、三专家 Workflow 和结果落库。
- `apps/api/tests/`：补充在线 Evidence 到 Analysis Pack / QA Gate 的集成测试和交叉验证失败重试测试。
- `docs/TODO.md`：本任务状态已更新；下一阶段转入 B3.8。

验收标准：

- 未配置真实 provider 时，接口返回 `available=false` 和明确原因。状态：已完成。
- 不把 deterministic wrapper 或 mock seed 包装成 LLM-backed execution。状态：已完成。
- Provider Adapter 支持 OpenAI-compatible Chat Completions、超时/网络/服务端错误边界和 JSON 输出解析。状态：已完成；使用测试替身验证，未出网。
- 专家模型按 Expert Registry 的模型档位路由，支持专家级和档位级环境变量覆盖。状态：已完成。
- 结构化输出按专家 Execution Contract 校验，失败结果不进入成功路径。状态：已完成。
- 执行请求必须绑定 Expert Registry、Execution Contract、Memory / Skill Context 和 Trace 边界。
- 真实 provider 配置完成后，至少 3 类专家输出结构化结果，并进入 Trace / Analysis Pack / QA Gate。状态：已完成；在线案例实际 QA 结果为 `rework`，仍需下一阶段补齐 Report Writer 交付验证。

## 当前下一步：B3.8 在线报告撰写与交付验证

在 B3.7 已完成的在线 Run 上，接入报告撰写专家（必要时按章节并行），仅允许使用通过 Evidence / Analysis Pack / QA Gate 的内容生成可追溯报告；当 QA 为 `rework` 时先保留风险状态或请求人工确认，不得直接标记为最终通过。

验收标准：

- 同一在线 Run 能从研究范围、Evidence、三类专家、交叉验证和 QA 进入 Report Writer。
- 报告章节保留 Claim、Evidence ID、来源 URL、风险和 QA 状态关联。
- QA `pass` 或 `pass_with_risk` 才能进入报告交付；`rework` 只能输出返工建议或待确认状态。

## Phase 0：开发前确认

阶段目标：

- 把技术路线、证据可信度、QA Gate、Research Memory 这些会影响后续实现的核心机制先定清楚。
- 机制细则沉淀在 `docs/MECHANISM.md`，TODO 只记录开发必须遵守的摘要和当前状态。

### 0.1 确认技术栈

任务：

- 确认前端框架。
- 确认后端 / Adapter 方案。
- 确认存储方案。
- 确认 Evolva 接入方式。

验收标准：

- 在 `docs/ARCHITECTURE.md` 中更新最终选择。
- 明确本地启动命令。
- 明确 mock 数据和真实数据切换方式。

状态：已确认并完成最小工程实现；前端为 Next.js，后端为 FastAPI Adapter，本地存储为 SQLite，Evolva 接入采用轻量 wrapper，不深改底层内核

### 0.2 细化证据可信度规则

任务：

- 定义 evidence confidence 评分维度和分值区间。
- 定义不同来源类型的基础分。
- 定义风险扣分项。
- 定义低 / 中 / 高可信阈值。

验收标准：

- 输出可实现的评分规则。
- 至少覆盖来源权威性、相关性、可复查性、时效性、具体性、多源支持、风险扣分。
- 能解释为什么不是简单“官网 90、评论 50”。

关键决策摘要：

- 可信度是“证据对当前分析任务的质量评分”，不是事实真伪的绝对判定。
- 采用规则评分为主、LLM 解释为辅的方向，避免纯主观打分。
- 高 / 中 / 低可信阈值采用 80 / 50。

状态：规则已确认，详见 `docs/MECHANISM.md`；已完成最小工程实现与测试，UI 仍需补充分维度解释展示

### 0.3 细化 QA Gate 规则

任务：

- 定义 QA Gate 评分维度。
- 定义 pass / rework 阈值。
- 定义最多返工 1 次后的处理策略。

验收标准：

- QA Gate 输出结构固定。
- 支持 pass / rework。
- rework 必须输出具体问题和改进建议。

关键决策摘要：

- QA Gate 检查 Analysis Pack，而不是等最终长报告生成后再检查。
- 输出 pass / rework、维度分数、问题、建议和返工次数。
- 返工最多 1 次；返工后仍不通过时生成带风险提示的报告或触发人工确认。

状态：规则已确认，详见 `docs/MECHANISM.md`；已完成最小工程实现与测试，未接真实返工 workflow

### 0.4 细化 Research Memory 规则

任务：

- 定义 P0 是否真正写入 Research Memory。
- 定义哪些内容可进入 Memory Candidate。
- 定义 candidate / active / quarantined / archived 状态转换。
- 定义记忆召回影响哪些专家或 workflow 环节。

验收标准：

- 明确知识库、证据库、历史报告、Memory、Skill 的边界。
- 明确 Memory 不是“把证据、报告、知识库内容都塞进上下文”。
- 明确 candidate 试用、active 生效、负反馈隔离和召回预算。
- 至少让一条 active memory 影响后续专家 checklist 或任务执行。

关键决策摘要：

- Research Memory 只保存能改善后续 Agent 判断和输出质量的执行经验，不自动保存高可信证据或 supported claim。
- 用户批注、知识库引用、QA 返工、交叉验证问题可以生成 Memory Candidate，但不自动 active。
- 产品语言使用“作用对象 / 生效策略”；当前代码内部仍保留 `target_agent / influence_target`，API 层优先暴露 `effect_strategy`。

状态：规则已确认，详见 `docs/MECHANISM.md`；已完成本地最小治理，后续增强见 Backlog B1

## Phase 1：Mock 形态复刻

阶段目标：

- 先复刻 Verity 的核心信息架构和页面形态，让主链路可被看见和点击。
- 所有 mock 数据必须明确保留 mock 边界，不得包装成真实在线采集能力。
- UI 视觉后续以 `docs/DESIGN.md` 和 `docs/verity-ui-design-preview.html` 为复刻目标继续细化。

关键产品决策摘要：

- 首页只保留自然语言调研输入和示例任务，不做复杂模式选择。
- 调研范围确认页是执行前 Human Gate。
- 调研执行页和报告阅读页采用左中右三栏结构。
- 报告页必须优先保证引用追溯和证据侧栏，而不是先堆图表。

视觉迁移状态（2026-07-16）：

- 工作台、调研范围确认、调研执行、报告阅读、决策链路、我的调研已按 `docs/verity-ui-design-preview.html` 迁移到 `apps/web`。
- 专家公会与专家详情沿用已完成的治理台视觉，并已确认新全局 Shell 未破坏其布局。
- 知识库与竞争情报中心在 UI Preview 中没有独立页面设计，当前只统一视觉并保留诚实占位，不伪造检索、图表或情报指标能力。

### 1.1 搭建 Web 应用骨架

任务：

- 创建 Web 应用。
- 建立全局导航。
- 建立基础路由。
- 接入 mock 数据。

验收标准：

- 可以本地启动。
- 左侧菜单包含工作台、我的调研、知识库、专家公会、竞争情报中心。
- 页面之间可跳转。

状态：Mock 形态已完成，已验证本地启动与路由跳转；未接真实 Evolva workflow

### 1.2 工作台首页

任务：

- 实现欢迎语。
- 实现一句话调研输入框。
- 实现示例任务卡片。
- 实现开始调研跳转。

验收标准：

- 首页不展示复杂模式配置。
- 输入需求后进入调研范围确认页。

状态：Mock 形态已完成；后续等待视觉细化与真实任务创建接入

### 1.3 调研范围确认页

任务：

- 展示 Agent 识别结果。
- 支持竞品标签选择、新增、删除。
- 支持分析维度选择。
- 支持报告视角、市场、用户、时间范围和补充说明。

验收标准：

- 第一层识别结果可预填。
- 用户确认后进入调研执行页。
- 页面体现 Human Gate。

状态：Mock 形态已完成；后续接入真实 scope preview / Human Gate 数据

### 1.4 调研执行页

任务：

- 实现左侧任务流水线。
- 实现中间专家动作流。
- 实现右侧实时证据库。
- 使用 mock 数据模拟执行过程。

验收标准：

- 可看到需求理解、编排派遣、证据采集、交叉分析、质检审查、报告撰写、签发交付。
- 证据卡片可展示来源和可信度。
- 完成后可进入报告页。

状态：Mock 形态已完成；后续接入真实 Agent workflow / evidence stream

### 1.5 报告阅读页

任务：

- 实现三栏布局。
- 左侧目录。
- 中间报告正文。
- 右侧证据 / 标注 / 知识库。
- 实现引用点击定位证据。

验收标准：

- 至少 3 条关键结论可点击追溯证据。
- 右侧证据卡片可打开 URL。
- 报告首屏包含核心统计和 QA 摘要。

状态：Mock 形态已完成；后续接入真实 report / evidence citation 定位

### 1.6 决策链路页

任务：

- 实现 Trace 总览。
- 实现阶段筛选。
- 实现步骤列表。
- 实现单步展开查看 Prompt / Input / Output。

验收标准：

- 展示总 token、耗时、步骤数。
- 可按阶段筛选。
- 单步详情可展开。

状态：Mock 形态已完成；后续接入真实 sanitized trace_steps

### 1.7 我的调研

任务：

- 实现报告卡片网格。
- 卡片展示标题、竞品、证据数、结论数、高置信数、时间。
- 提供报告、决策链路、图谱入口。

验收标准：

- 可从列表打开报告。
- 可从列表打开决策链路。
- 每个报告有独立 URL。

状态：Mock 形态已完成；后续接入 SQLite reports

### 1.8 专家公会

任务：

- 实现专家卡片列表。
- 支持层级筛选。
- 支持专家详情。

验收标准：

- 专家按决策层、策略层、执行层展示。
- 每个专家显示职责、工具范围、输出 Schema 摘要。

状态：Mock 形态已完成；后续接入 expert_agents 配置与详情

## Phase 2：结构化数据与业务机制

阶段目标：

- 把 UI mock 背后的核心业务对象结构化，让 Evidence -> Claim -> Analysis Pack -> QA Gate -> Report 的链路可解释、可测试。
- 优先实现规则化、可验证的最小机制，不依赖真实在线抓取或完整 LLM workflow。

关键产品决策摘要：

- Evidence Confidence 是证据质量评分，不是事实真伪判定。
- 核心 Claim 必须尽量绑定 Evidence；低可信、冲突、缺证据的 Claim 要降级或标记风险。
- Report Writer 后续只能基于通过 QA 的 Analysis Pack 写报告，不应新增未绑定证据的核心结论。
- QA Gate 返工最多 1 次，避免无限循环。

### 2.1 建立 SQLite Schema

任务：

- 建立 reports。
- 建立 expert_agents。
- 建立 evidence_items。
- 建立 claims。
- 建立 analysis_packs。
- 建立 qa_gate_results。
- 建立 trace_steps。
- 建立 annotations。
- 建立 research_memories。

验收标准：

- mock 数据可以写入数据库。
- 页面从数据库读取，而不是只读静态对象。

状态：已完成最小实现；SQLite schema 已建立，当前数据为 mock seed，API 与部分页面已从 local-db 读取；未接真实 Evolva workflow

### 2.2 实现 Evidence Scoring

任务：

- 实现证据评分函数。
- 保存维度分数。
- 在 UI 展示总分和风险提示。

验收标准：

- 同一条证据可以解释分数来源。
- 低可信证据不会支撑强结论。

状态：已完成最小实现；规则评分函数与维度分测试已建立，UI 仍需进一步展开显示完整分数来源

### 2.3 实现 Analysis Pack

任务：

- 定义 Analysis Pack JSON Schema。
- 将 evidence 转换为 claim。
- 建立 claim-evidence 绑定。
- 标注数据缺口和冲突。

验收标准：

- 每个关键 claim 至少可绑定一个证据。
- unsupported / conflicted claim 可被识别。

状态：已完成最小实现；已提供 Analysis Pack 组装函数与只读 API，当前 Claim 仍来自 mock seed / 规则结构化，不是 LLM 自动生成

### 2.4 实现 QA Gate

任务：

- 对 Analysis Pack 执行评分。
- 输出 pass / rework。
- 支持最多返工 1 次。

验收标准：

- 低证据充分性会触发 rework。
- rework 输出具体建议。
- 返工次数可记录。

状态：已完成最小实现；已提供规则 QA Gate 与测试，支持 pass / rework 和最多返工 1 次的结构字段，未接真实返工 workflow

## Phase 3：接入 Evolva

阶段目标：

- 在不深改 Evolva 底层核心逻辑的前提下，确认 Verity 如何复用 Evolva 的 Workflow / Loop / Trace / Memory / Skills 能力。
- 先用轻量 Adapter / wrapper 做最小可验证接入，再逐步替换 mock 和 deterministic wrapper。

关键产品决策摘要：

- Verity 的专家必须保留为多 Agent 架构，不能退化为单 Agent + 多个 Skill。
- Skill 是 Agent 可调用的方法、知识、Prompt 片段或 checklist，不是专家本体。
- Evolva 默认角色不直接暴露为 Verity 产品角色；Verity 在 Adapter 层定义 Research Orchestrator、领域专家、Cross-validation、QA、Report Writer 等产品专家。
- 当前 P3 的真实边界是 wrapper / smoke trace / deterministic expert execution，不等同于真实在线研究 workflow。

### 3.1 调研 Evolva 接入点

任务：

- 确认 Evolva Workflow / Loop 调用方式。
- 确认 Trace 数据位置和格式。
- 确认 Memory / Skill 读写方式。
- 确认工具调用边界。

验收标准：

- 写出接入说明。
- 明确哪些能力复用，哪些能力 wrapper。

状态：已完成；接入点说明见 `docs/EVOLVA_INTEGRATION.md`，已确认 Workflow / Loop / Trace / Memory / Skills / Multi-Agent 的源码入口和 wrapper 边界

### 3.2 接入 Trace

任务：

- 将 Evolva trace event 映射为 trace_steps。
- 实现脱敏。
- 在决策链路页展示真实或半真实 Trace。

验收标准：

- 至少能展示一次真实 workflow 的步骤。
- Prompt / Input / Output 可追溯。

状态：已完成最小接入；已实现 Evolva trace 到 Verity trace_steps 的脱敏映射、smoke trace API 和决策链路页 API 读取。当前是 Evolva TraceRecorder 级验证，不等同于真实竞品研究 workflow

### 3.3 接入 Expert Agent

任务：

- 将专家配置映射为本地 Expert Agent。
- 实现专家 Agent 选择。
- 实现只读专家 Agent 并行执行的最小 wrapper。
- 保留 Skill 作为专家 Agent 可调用的方法、知识或工具规范。

验收标准：

- 至少 3 个专家 Agent 可参与一次调研。
- 至少 2 个互不依赖的专家 Agent 可并行执行。
- 并行结果能汇总进入 Analysis Pack。

状态：已完成最小实现；已在 Verity Adapter 层定义产品专家角色，支持至少 7 个专家、3 个只读专家并行 wrapper，并将结果汇总进入 Analysis Pack / QA Gate。当前为 deterministic local-db wrapper，不等同于真实在线研究。已完成 B3.1 / B3.2 Expert Registry 与只读 API，下一步按 B3.3 补系统模块契约。

### 3.4 接入 Memory

任务：

- 将 Research Memory candidate 写入本地表。
- 按规则写入 Evolva Memory 或保持本地治理。
- 实现召回对报告风格或专家选择的最小影响。

验收标准：

- 记忆不是单纯存档，至少影响一次后续任务。
- 低置信记忆不会进入 active。

状态：已完成最小实现；支持用户反馈生成 Memory Candidate、candidate / active / quarantined / archived 状态治理，active expert_lesson 可影响目标专家 checklist；支持知识库条目作为 evidence source，并以 candidate trial 低权重试用；已限制每个专家 active/candidate 召回数量。当前仅本地治理，未自动同步外部 MemoryStore

## Phase 4：P1 增强

阶段目标：

- 在 P0 主链路可跑、核心机制可解释之后，增强报告阅读、知识沉淀、图表数据和竞争情报中心。
- P4 不应抢在真实 workflow 和端到端验证之前制造无法解释的复杂图表或夸大指标。

关键产品决策摘要：

- 图表必须绑定数据表和证据来源，不能生成没有数据依据的可视化。
- 标注 / 批注 / 加入知识库是知识沉淀入口，但知识库本身不是 Research Memory。
- 知识库内容可以作为专家采集证据的候选来源，但必须以 `user_knowledge` 等来源类型区分。

### 4.1 图表与数据表

任务：

- 支持雷达图、柱状图、环形图。
- 每个图表绑定数据表。
- 支持 CSV 导出。

验收标准：

- 图表可追溯数据来源。
- 推断数据有显式标注。

状态：待开始

### 4.2 标注、批注、知识库

任务：

- 支持正文选中文字。
- 支持亮点、认同、存疑、待办标注。
- 支持添加批注。
- 支持加入知识库。

验收标准：

- 右侧可查看批注。
- 点击批注可定位正文。
- 加入知识库后可在知识库页检索。

状态：待开始

### 4.3 知识图谱

任务：

- 基于 report-claim-evidence 生成图谱。
- 支持拖拽和缩放。
- 点击节点查看详情。

验收标准：

- 报告节点、结论节点、证据节点三层可见。
- 点击证据可打开来源。

状态：待开始

### 4.4 竞争情报中心

任务：

- 实现核心指标卡。
- 实现报告概览。
- 实现信源结构。
- 实现专家贡献统计。

验收标准：

- 指标来自真实结构化数据。
- 不展示无法解释的夸大指标。

状态：待开始

## Phase 5：验证与复盘

阶段目标：

- 用真实或半真实竞品研究主题验证 Verity 的主链路，而不是只停留在页面和 mock 数据。
- 通过 bad case 反推证据可信度、QA Gate、Trace、Memory 是否真的有用。
- 简历或项目结果中的效率、证据数量、信源数量等指标必须来自本阶段验证，不能提前编造。

关键产品决策摘要：

- 验证重点不是“生成一篇漂亮报告”，而是证明报告结论可追溯、质量门控可解释、Agent 过程可复盘、Memory 能影响下一次执行。
- 至少记录 3 个 bad case，并说明机制如何发现或修复问题。

### 5.1 端到端案例验证

任务：

- 选择一个竞品研究主题。
- 跑通从输入到报告的完整流程。
- 记录成功路径和 bad cases。

验收标准：

- 有一份完整可打开报告。
- 有证据库。
- 有 QA Gate 输出。
- 有 Trace。
- 有至少 3 个可解释 bad case。

状态：待开始

### 5.2 产品复盘

任务：

- 复盘专家选择是否合理。
- 复盘证据置信度规则是否够用。
- 复盘 QA Gate 是否发现了真实问题。
- 复盘 Memory 是否真的影响后续执行。

验收标准：

- 输出 Validation Report。
- 更新 DECISION_LOG。
- 更新后续 TODO。

状态：待开始

## Backlog：已讨论但延后

本节记录已经形成方向、但不属于当前最小实现范围的后续事项。避免后续迭代时丢失已讨论决策。

### B1 Memory 系统增强

任务：

- 将当前 `target_agent / influence_target` 内部字段逐步迁移为更贴近产品语言的 `作用对象 / 生效策略`，API 与 UI 层优先使用 `effect_strategy`。
- 实现 Memory Candidate 的试用记录详情，包括使用在哪次任务、哪个专家、是否进入报告、用户是否删除或负评、QA 是否通过。
- 实现 candidate 多次正向试用后的升级建议，但不得自动 active。
- 实现 active memory 的过期、降权、回滚和归档策略。
- 将用户删除知识库引用、批注“不合适”等负反馈接入 Memory Candidate 降权 / quarantine。
- 后续评估是否将 active memory 同步到 Evolva MemoryStore；同步必须是显式动作，不自动发生。
- 后续评估将已验证专家经验沉淀为 Skill / checklist 文件，而不只是存在 SQLite。
- 增加 Memory 管理页面：查看 candidate、active、quarantined，支持激活、隔离、归档和回滚。

验收标准：

- Candidate trial 有可审计记录。
- Active memory 的召回、使用和回滚可追踪。
- Memory 不因知识库、高可信证据或 supported claim 自动膨胀。
- 用户负反馈能阻止错误记忆继续影响专家。

状态：待后续增强；当前仅完成本地最小治理与专家 checklist 影响。

### B2 真实 Agent Workflow 接入

任务：

- 修复 / 安装完整 Evolva runtime 依赖，例如当前缺失的 `langgraph`。
- 将 Verity Research Orchestrator 生成的 workflow spec 接入 Evolva WorkflowEngine。
- 将真实 workflow output 写入 evidence / claims / analysis_pack / trace_steps。
- 将 smoke trace 替换为至少一次真实或半真实 research workflow trace。

验收标准：

- 至少一次真实 workflow run 可在决策链路页展示。
- Workflow 结果能进入 Analysis Pack 和 QA Gate。
- Mock seed、local-db、evolva workflow 三种来源明确区分。

状态：已完成最小受控接入；已补齐本地 `langgraph` runtime，并新增 Evolva `WorkflowEngine` 驱动的版本化本地证据 workflow。该 workflow 会将规则评分后的 Evidence、Claim、Analysis Pack、QA Gate 和脱敏 Trace 写入 Verity SQLite，接口显式标注 `is_real_workflow=true`、`is_real_research=false`。仍未完成真实在线研究 workflow。

### B3 专家 Agent 与并行执行增强

任务：

- B3.1 Expert Registry：将已确认的专家契约落成只读专家注册表，包括研究编排专家、证据采集专家、产品分析专家、定价策略专家、用户体验分析专家、交叉验证专家、QA 质检专家、报告撰写专家。状态：已完成，见 `apps/api/verity_api/expert_registry.py`。
- B3.2 Expert Registry API：提供 `/api/experts` 与 `/api/experts/{id}`，返回中文名称、层级、职责、行为边界、工具权限、输出 Pack 类型、是否支持多实例、Memory / Skill 治理摘要。状态：已完成，已覆盖 API 测试。
- B3.3 系统模块契约：为 Evidence Router / Evidence Slice、QA Brief Builder、Report Renderer 建立工程配置或 schema，明确它们不是专家本体。状态：已完成，见 `apps/api/verity_api/system_module_registry.py`。
- B3.4 Prompt / schema 草稿：基于 Expert Registry 为各专家生成 LLM-backed execution 的输入输出 schema 和 prompt fragment，但不把 prompt 暴露为页面可自由编辑项。状态：已完成，见 `apps/api/verity_api/expert_execution_contracts.py`。
- B3.5 并行执行增强：按竞品、维度、Evidence Slice、Claim 数量和 token 预算拆分同类型专家实例，并将 fragment 合并为稳定 Pack。状态：已完成，见 `apps/api/verity_api/expert_instance_planner.py`。
- B3.6 Memory / Skill 接入：将 active memory 以受控 checklist / prompt context 注入目标专家；candidate memory 只按目标专家低权重试用；Skill 只使用经过治理的版本化方法。状态：已完成，见 `apps/api/verity_api/expert_context.py`。
- B3.7 LLM-backed expert execution：逐步替换 deterministic expert wrapper，至少让 3 类专家输出真实结构化结果，并写入 Trace / Analysis Pack / QA Gate。状态：Provider Adapter、专家模型路由、结构化输出校验、单专家 `/execute`、Trace 追加边界和三专家本地 Evidence Workflow 已完成；Tavily 公开网页采集适配也已完成，但在线 Evidence 尚未接入该 Workflow，在线案例仍待验证。

验收标准：

- B3.1 / B3.2：专家注册表和只读 API 可测试；专家公会后续可从 API 获取治理信息。
- B3.3：Evidence Router、QA Brief Builder、Report Renderer 在工程上与专家类型区分清楚。
- B3.4：每类专家具备独立输入输出 schema 草稿，且与 `docs/MECHANISM.md` 对齐。
- B3.5：至少 2 个同类型专家实例可并行执行并合并 fragment。
- B3.7：至少 3 个专家输出真实结构化结果，且可追溯到 Trace 和 Analysis Pack。

状态：机制已确认，详见 `docs/MECHANISM.md` 第 1 章；B3.1-B3.6 已完成。B3.7 的本地 Evidence 验收已完成，在线 Evidence 采集适配已完成；当前唯一未完成的验收是：同一个在线 Run 中，让 Tavily Evidence 经过至少 3 类真实专家、交叉验证和 QA Gate，并可追溯到最终结果。完成前 B3.7 保持“部分完成”。

### B4 知识库作为证据源增强

任务：

- 实现知识库检索，而不是只使用 seed knowledge item。
- 支持专家从知识库命中条目并转化为 `source_type = user_knowledge` 的 evidence。
- 在报告阅读页右侧证据栏展示用户知识库来源。
- 支持用户删除引用、标注不合适、保留引用，并将反馈回写到 candidate trial。

验收标准：

- 知识库引用能在报告证据栏定位。
- 用户负反馈能影响对应 Memory Candidate 状态。
- 知识库内容不会常驻上下文，只按需检索。

状态：待后续增强；当前仅完成 seed 知识库引用为 evidence 的 API。

### B5 端到端验证与指标

任务：

- 选择一个真实竞品研究主题，跑通从输入到报告的端到端案例。
- 记录耗时、证据数量、信源数量、QA rework、Trace 步骤和 Memory 使用情况。
- 基于真实案例再决定是否能写效率提升、证据规模和信源覆盖指标。

验收标准：

- 结果指标来自真实验证，不使用未验证的简历数字。
- 至少记录 3 个 bad case 和对应机制改进。

状态：待 Phase 5 验证。
