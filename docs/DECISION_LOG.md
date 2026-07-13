# AI Product Research Agent Console Decision Log

版本：v0.1  
状态：开发前决策记录  
说明：本文件记录已经讨论过的重要产品、架构和范围决策。后续新增或修改决策时，应追加记录，不要只依赖聊天上下文。

记录原则：

- Decision Log 是产品决策版本史，不是永久禁令清单。
- 对阶段性决策，应尽量标注状态和适用范围，例如 `active`、`phase-bound`、`needs-review`、`superseded`，以及 `P0`、`P1`、`UI mock 阶段`、`真实接入前` 等。
- 如果用户最新明确指令改变了某条阶段性决策，应更新该条适用范围或追加新决策，而不是机械阻塞开发。

## 2026-07-10

### D001：项目定位为 Evolva 之上的 AI 产品研究工作台

决策：

- 本项目不从零实现 Agent Infra。
- Evolva 作为底层 Agent Infra 和学习对象。
- 本项目补充 Web 产品层、竞品研究业务层和可视化工作台。

原因：

- 用户目标是 AI 产品经理能力提升，不是 Agent Runtime 工程实现。
- Evolva 已覆盖 Loop、Tools、Trace、Eval、Guardrails、Memory、Skills 等底层概念。
- Web 层可以更好体现 PM 对 Agent Workflow 的产品化理解。

影响：

- 优先做业务流程、证据链、Trace、质检和报告体验。
- 不优先深改 Evolva 内核。

### D002：采用复刻式学习路线

状态：active  
适用范围：长期学习方法

决策：

- 采用参考式学习路线：参考 Verda 学习产品形态和交互，参考 Evolva 学习 Agent Infra，参考 InsightFlow 学习竞品分析 workflow。
- 不做机械复刻，最终应沉淀为 Verity 自己的产品架构、证据机制、Trace 机制和设计系统。
- 重点是通过参考项目理解模块价值和产品决策，而不是只抄 UI 或搬运实现。

原因：

- 该项目主要用于学习和能力证明，不用于公开商业发布。
- 复刻可以降低从零设计的不确定性。

影响：

- 可以先 mock 页面，再逐步接真实 Agent Workflow。
- 必须理解并沉淀每个模块的产品决策，不能只抄 UI。

### D003：专家库抽象为 Expert Agent Library

决策：

```text
Expert Agent = Role + Goal + Tool Scope + State + Output Schema + Trace
```

专家应设计为可被主控 workflow 调度的任务型 Agent，而不是单纯的 Skill 或角色 Prompt。Skill 保留为专家 Agent 可调用的方法、知识、Prompt 片段或工具使用规范。

原因：

- 本项目需要体现多 Agent 编排能力，不能在记忆系统已经轻量的情况下继续弱化专家协作。
- 竞品研究中的采集、分析、验证、质检、撰写可以拆成多个有独立目标、状态、输入输出和 Trace 的任务型 Agent。
- Skill 本身更适合作为能力模块，不适合作为“专家本体”的唯一抽象。

影响：

- 专家公会页面展示 Expert Agent。
- 执行时由主控 workflow 选择和调度专家 Agent。
- 多 Agent 协作体现在并行执行、独立 Trace、共享证据库、结构化输出、汇总质检和返工闭环上。
- Skill 可以作为专家 Agent 的内置能力或可复用方法沉淀。

待确认：

- 专家 Agent 配置文件格式。
- 专家是否允许用户自定义。

### D004：支持并行专家组，但限定为只读分析任务

决策：

- 对互不依赖的只读任务，支持并行专家分析。
- 对依赖前置结果、写文件、Shell、高风险工具的任务，不默认并行。

原因：

- 竞品研究天然包含多视角并行分析。
- 顺序执行会增加等待时间。
- 无边界并行会带来共享状态污染和工具风险。

影响：

- 需要设计 Parallel Expert Group。
- 并行输出必须经过 Reviewer / Synthesizer 汇总。

待确认：

- 并行能力放在 Adapter 层还是改 Evolva 底层。

### D005：数据获取不以绕过反爬为能力

决策：

- 不把绕过抖音、小红书、微博等平台反爬作为产品能力。
- 优先使用公开网页、搜索结果、用户上传、授权数据、第三方服务和示例数据。
- 无法获取的数据必须标注缺口。

原因：

- 反爬绕过合规风险和稳定性风险高。
- 演示截图不能作为真实能力假设。
- 竞品研究的可信度来自证据链和缺口说明。

影响：

- 报告中不默认宣称“全网舆情”。
- 更稳妥使用“用户反馈 / 公开反馈”。

### D006：证据可信度必须专业设计

状态：active  
适用范围：真实 Evidence Scoring、Claim QA、Report Gate 接入前必须满足；UI mock 阶段可用明确标识的示例分数

决策：

证据可信度采用多维度规则框架：

- 来源权威性。
- 内容相关性。
- 可复查性。
- 时效性。
- 信息具体性。
- 多源支持。
- 风险扣分。

原因：

- 简单“官网 90 分、评论 50 分”会显得 toy。
- 面向 PM 的项目更看重机制设计是否可解释。

影响：

- 在实现真实 Evidence Scoring / Claim QA / Report Gate 前，必须细化评分规则。
- UI 原型阶段可以使用明确标识的 Mock 分数，但不得包装为真实评分能力。
- LLM 可做摘要和解释，但不应完全主观打分。

待确认：

- 每个维度的分值区间。
- 不同 claim 类型下的证据权重。

### D007：报告前需要 Analysis Pack 和 QA Gate

决策：

报告生成前先形成 Analysis Pack，再由 QA Gate 质检。

Analysis Pack 包含：

- 竞品知识 Schema。
- 结构化论点。
- 证据绑定。
- 置信度。
- 数据缺口。
- 潜在冲突。

QA Gate 输出：

- pass / rework。
- 维度评分。
- 问题。
- 改进建议。

原因：

- 质检员质检的是“报告素材包”，不是最终长文。
- 这样可以避免弱证据直接进入最终报告。

影响：

- Report Writer 只能基于通过质检的 Analysis Pack 写报告。
- QA Gate 是 P0 核心链路。

### D008：返工最多 1 次

状态：active  
适用范围：P0 / MVP 默认策略

决策：

- QA Gate 不通过时允许返工。
- P0 / MVP 默认最多返工 1 次。
- 返工后仍不通过，应生成带风险提示的报告或请求人工确认。
- 后续如引入人工确认、显式配置或批处理模式，可以扩展返工策略，但必须有上限并记录 Trace。

原因：

- 防止 Agent 无限循环。
- 保持 workflow 可控。

影响：

- trace_steps 和 qa_gate_results 需要记录 rework_count。

### D009：报告是可交互研究档案，不是纯长文

状态：active  
适用范围：P0 先保证可追溯阅读，P1/P2 再增强编辑和知识沉淀能力

决策：

报告页采用三栏结构：

- 左侧目录。
- 中间正文。
- 右侧证据 / 标注 / 知识库。

P0 必须支持：

- 引用定位。
- 质检摘要。
- 证据侧栏。

P1 / P2 扩展：

- 图表 + 数据表。
- 标注、批注、加入知识库。
- 段落编辑。

原因：

- 竞品研究价值在于证据可复查、图表可解释、结论可追溯。
- Verda 的报告形态值得学习。

影响：

- 报告结构不固定死，采用模块化报告。
- 图表必须绑定数据表。

### D010：决策链路是 P0 核心功能

状态：active  
适用范围：P0 起必须有用户可理解的决策链路；原始日志不直接等同于用户界面

决策：

- 报告页提供决策链路入口。
- 决策链路展示用户可理解、已脱敏、可审计的关键 Agent Trace。
- 单步可展开 Prompt / Input / Output。
- 原始日志可保留在系统内部，不直接作为用户界面展示。

原因：

- Agent 产品必须可追溯、可调试、可审计。
- 这是区别于普通 AI 报告生成器的关键能力。

影响：

- 需要将 Evolva trace 映射为 PM 可读 Trace。
- 展示前必须脱敏。

### D011：我的调研和报告独立 URL 是基础能力

状态：active  
适用范围：P0 需要稳定可访问标识，正式 Web 版本升级为独立 URL

决策：

- 每份报告作为独立研究资产保存。
- 我的调研页管理历史报告。
- P0 应保证每份报告有稳定可访问标识。
- 本地 MVP 可使用本地路由、报告 ID 或文件 ID；正式 Web 版本再升级为独立 URL。

原因：

- 报告不是一次性输出。
- 后续知识图谱、情报中心、记忆都依赖历史资产。

影响：

- reports 表和路由设计应支持持久化和后续独立 URL 升级。

### D012：知识库不等于 Memory

决策：

- 知识库保存用户主动标注、收藏、加入的内容资产。
- Evidence Library 保存 Agent 采集证据。
- Research Memory 保存会影响下一次 Agent 行为的长期记忆。

原因：

- 只存数据不是 Agent Memory。
- 记忆必须影响任务理解、专家选择、质检、报告风格或风险判断。

影响：

- 需要单独设计 Research Memory Schema。
- 加入知识库不自动等于写入 active memory。

### D013：记忆系统需要作为重点产品决策设计

状态：active  
适用范围：真实 Research Memory 接入前必须单独设计

决策：

- 本项目需要设计 Research Memory Layer。
- MVP 可以先实现数据结构和候选写入规则。
- 后续再考虑 mem0 等专业记忆系统。
- Research Memory 需要单独设计 Schema、候选写入、召回、治理和回滚；具体记录位置可在 TODO、Architecture 或后续 Memory 设计文档中维护。

原因：

- Agent 产品经理需要理解记忆该记什么、何时召回、如何治理。
- 错误记忆会污染后续分析。

影响：

- 不能把证据库、知识库或历史报告直接等同于 Agent Memory。
- Memory 相关设计需要能说明其如何影响后续任务理解、专家选择、质检或报告风格。

### D014：首页保持简单，复杂配置后置到调研范围确认页

决策：

- 首页只保留自然语言输入、示例任务和专家协作氛围。
- 不在首页做快速 / 普通 / 专家模式。
- 不在首页展开复杂分析模块选择。

原因：

- 首页的职责是发起任务，不是完整配置。
- 调研范围确认页更适合承载 Human Gate。

影响：

- 工作台首页 UI 简化。
- 调研范围确认页承担竞品、维度、视角、市场、用户、时间范围配置。

### D015：视觉规范文档的生成时机

状态：superseded by 2026-07-10 design baseline  
适用范围：设计未定稿前不主动生成；设计确认后可沉淀为正式规范

决策：

- 在视觉规范未确认前，不由 Codex 主动生成 `DESIGN.md`。
- 页面视觉方向优先由用户或 Gemini 提供，并经用户确认。
- 当用户确认设计产物后，可以将其沉淀为 `docs/DESIGN.md`，作为后续 UI 开发的必读上下文。

原因：

- 用户希望用 Gemini 做视觉设计和规范生成。
- 视觉规范需要等设计方向定稿后再固化，避免过早文档化。

影响：

- 2026-07-10 已根据用户确认的 `docs/verity-living-design-system.html` 生成 `docs/DESIGN.md`。
- 后续 UI 开发应读取 `docs/DESIGN.md`，但不得用视觉规范覆盖产品真实性、证据链、Trace 和 Memory 边界。

### D016：P0 技术栈采用 Next.js + FastAPI + SQLite

状态：active  
适用范围：P0 本地开发与第一版 Web 产品层

决策：

- 前端采用 Next.js + React + Tailwind。
- 后端 / Adapter 采用 Python FastAPI。
- 存储采用 SQLite。
- 数据源分为 `mock`、`local-db`、`evolva` 三层。
- Evolva 接入优先通过 Adapter / wrapper，不深改 Evolva 底层。

原因：

- Next.js 适合多页面、报告独立访问、三栏布局和后续前端产品形态。
- FastAPI 更贴近 Evolva Python 代码，后续接 Workflow、Trace、Memory、Skills 和 Tools 更自然。
- SQLite 对本地单用户学习项目足够轻量，适合结构化证据、报告、claim、trace 和 memory。

影响：

- 本地启动会包含前端和 FastAPI 两个服务。
- Phase 1 / 2 先建立 Verity 业务数据结构，Phase 3 再接 Evolva。
- Mock 能力必须通过数据源层显式标注，不能包装为真实采集。

### D017：核心产品机制沉淀到 MECHANISM.md

状态：active  
适用范围：Evidence Scoring、QA Gate、Claim-Evidence Binding、Research Memory、Decision Trace

决策：

- `docs/MECHANISM.md` 作为核心产品机制的主文档。
- `docs/ARCHITECTURE.md` 只保留工程落地结构，并引用机制文档。
- `docs/TODO.md` 记录机制规则确认和工程实现状态。

原因：

- Evidence Scoring、QA Gate 和 Memory 既是产品能力，也是后续面试需要清晰解释的机制。
- 单独文档更便于复习、实现和迭代，避免把产品机制淹没在架构细节中。

影响：

- 后续调整证据评分、QA 阈值、Memory 状态流转时，优先更新 `docs/MECHANISM.md`。
- 工程实现必须能追溯到 `docs/MECHANISM.md` 中的规则。

## 2026-07-13

### D018：B3 专家契约与运行实例机制已确认

状态：active  
适用范围：B3 Expert Registry、LLM-backed expert execution、专家公会真实数据接入前

决策：

- Verity 的专家是治理层面的 Agent 类型，运行时可按竞品、维度、Evidence Slice、Claim 数量和 token 预算拆成多个同类型 Agent 实例。
- 专家公会展示长期治理信息；Trace 展示单次运行事实和实际启动的实例。
- 已确认专家类型包括：研究编排专家、证据采集专家、产品分析专家、定价策略专家、用户体验分析专家、交叉验证专家、QA 质检专家、报告撰写专家。
- Evidence Router / Evidence Slice、QA Brief Builder、Report Renderer 是系统模块，不是专家本体。
- 对外展示的工具权限必须是具体工具，例如公开网页搜索、用户 URL 读取、报告渲染器；任务派遣、Trace 写入、Memory 状态流转等属于内部能力，不作为用户可开关工具展示。
- 默认采用“慢但稳”的专业研究模式，允许通过分批、多实例、合并和 Trace 记录换取证据覆盖、引用稳定和结论可复查。

原因：

- 防止把多 Agent 架构退化为单 Agent + 多个 Skill。
- 防止把专家详情页做成 Prompt Playground、工具安装器或 Memory 编辑器。
- 防止上下文爆炸：专家最终覆盖全部相关证据，但单轮只处理受控 Evidence Slice / QA Brief /章节输入。
- 让后续工程实现有清晰的 Expert Registry、系统模块和运行实例边界。

影响：

- `docs/MECHANISM.md` 第 1 章作为专家契约细节来源。
- `docs/TODO.md` 中 B3 已拆分为 Expert Registry、专家 API、系统模块契约、prompt/schema、并行实例、Memory/Skill 接入和 LLM-backed execution。
- 下一步应先实现只读 Expert Registry 与 API，再逐步接真实 LLM-backed expert execution。
