# Verity Core Product Mechanisms

版本：v0.1  
状态：P0 机制规则已确认，待工程实现  
关联文档：`docs/ARCHITECTURE.md`、`docs/TODO.md`、`docs/DECISION_LOG.md`

本文档记录 Verity 的核心产品机制，重点用于后续开发实现、产品复盘和面试复习。它回答的问题是：Verity 为什么不是普通竞品报告生成器，以及 Evidence、Claim、QA、Trace、Memory 如何形成可解释闭环。

## 1. 机制总览

Verity 的核心链路是：

```text
Research Goal
  -> Scope Confirmation
  -> Research Plan
  -> Evidence Library
  -> Evidence Scoring
  -> Evidence Router / Evidence Slice
  -> Claim-Evidence Binding
  -> Analysis Pack
  -> QA Gate
  -> Report
  -> Decision Trace
  -> Research Memory Candidate
```

关键原则：

- Evidence Scoring 不是判断网页绝对真假，而是评估证据是否适合支撑当前竞品分析任务。
- Claim 必须尽量绑定 Evidence。
- Analysis Pack 是报告生成前的结构化素材包。
- QA Gate 检查 Analysis Pack，而不是等报告写完后再补救。
- Decision Trace 是面向用户的决策回放，不是原始日志倾倒。
- Research Memory 必须影响后续 Agent 行为，否则只是存档。
- 专家是治理层面的 Agent 类型；运行时可根据竞品、维度、Evidence Slice、Claim 数量和 token 预算拆成多个同类型 Agent 实例。实例并行提升覆盖度，最终必须合并为一个稳定 Pack。

### 1.1 研究编排专家执行契约

研究编排专家属于 L3 决策层。它的职责不是研究竞品事实或撰写结论，而是在 Human Gate 确认范围后，将研究目标转化为可执行、可审计的多 Agent 计划。

**触发时机**

- 用户确认调研范围后启动一次。
- QA Gate 首次要求返工时，可基于明确问题生成一次修订计划。
- 不因“继续多找信息”自行无限重规划；返工仍遵守最多 1 次的全局规则。

**输入**

- 已确认的研究目标、竞品、分析维度、市场、时间范围与补充要求。
- 用户主动提供的 URL / 附件清单。
- 允许来源边界：公开、可访问网页，以及用户主动提供的 URL / 附件；不把搜索摘要直接作为 Evidence。
- 专家注册表、相关 Active Memory、与本次范围相关的 Candidate Memory 可试用提示，以及已有 QA 返工问题（如有）。

**输出：Research Plan**

```text
Research Plan
├─ 调研范围摘要
├─ 每个维度要回答的问题
├─ 被派出 / 未被派出专家及原因
├─ 专家任务、并行组与前后依赖
├─ 预期 Evidence 类型与来源边界
├─ 已知数据缺口与风险
├─ 使用的 Memory / Skill
└─ 计划版本与是否为返工版本
```

**行为边界**

- 只围绕 Human Gate 已确认的范围规划，不得静默增加竞品、市场或分析维度。
- 选择完成任务所需的最少专家集合；不为展示多 Agent 而全员派出。未选择“用户体验 / 用户反馈”维度时，不派出用户体验分析专家。
- 互不依赖的只读分析任务可以并行；证据汇总、交叉验证、QA 和报告撰写必须按依赖顺序执行。
- 不直接采集网页、不直接生成 Evidence、Claim 或最终报告，也不将用户输入中的无来源断言写入证据库。
- 证据不足时在计划中声明 `data_gap`，不能要求下游专家强行得出结论。

**工具与内部能力的边界**

专家详情页只展示用户可理解的具体工具授权，例如“公开网页搜索”“用户 URL 读取”“代码执行器”。任务派遣、计划写入、Trace 记录、报告交接、Memory 状态流转属于系统内部执行能力，不作为对外工具权限展示。

P0 中，研究编排专家不拥有公开网页搜索、用户 URL 读取或代码执行器等外部资料工具；这些工具按职责授予证据采集专家或相关分析专家。它可读取已确认范围、专家注册表与允许的 Memory，并调用系统内部的工作流派遣能力。

**Memory 与 Skill**

- Active Memory：可直接影响研究重点、专家选择与风险偏好。
- Candidate Memory：编排专家只读取与当前范围匹配的目标专家、作用对象和相关性提示；候选内容全文仅由其目标专家以低权重试用。Candidate 不得自行扩大范围、改变来源规则或成为事实依据。
- P0 不要求为编排专家预置多个 Skill。调研范围、来源边界、QA 返工上限等属于系统机制或岗位契约，不应被伪装成 Skill。后续仅当“调研计划检查”被证明是可独立复用、可评估的方法时，才可沉淀为版本化 Skill。

**Trace 要求**

至少记录脱敏后的范围摘要、派出与未派出专家及原因、并行组和依赖关系、引用的 Memory / Skill、计划版本，以及 QA 返工原因（如有）。

### 1.2 证据采集专家执行契约

证据采集专家属于 L1 执行层。它负责将编排专家的证据计划转化为可复查、可评分、可绑定 Claim 的 Evidence；它不是“搜索几个链接后返回 URL”的助手。

**输入**

- 编排专家输出的证据计划：研究对象、分析维度、待回答问题、优先来源类型与每个维度的默认采集预算。
- 用户主动提供的 URL / 附件清单。
- 允许来源边界：公开、可访问网页，以及用户主动提供的 URL / 附件。

**执行链路**

```text
检索或读取 URL
  -> 候选来源
  -> 来源筛选与实际页面读取
  -> 提取关键原文片段与元信息
  -> Evidence Candidate
  -> 规则评分
  -> 可用 Evidence 进入共享证据库
```

搜索结果只用于发现候选 URL；只有实际成功读取的页面或附件中的关键原文片段，才能成为 Evidence。LLM 摘要仅用于帮助阅读，不能替代原文片段或单独支撑 Claim。

**来源与工具边界**

- 优先来源：官网、产品页、定价页、帮助中心、更新日志、公开报告，以及用户主动提供的 URL / 附件。
- 允许展示的具体工具权限：公开网页搜索、公开网页读取、用户 URL 读取、用户附件读取；代码执行器 P0 禁用。
- 不登录、不绕过反爬、不处理验证码，不把付费墙或搜索摘要伪装成正文证据。
- 任务派遣、Evidence 写入、Trace 记录与评分调用均属于内部执行能力，不作为专家详情页的对外工具清单。

**Evidence 最小结构**

```text
Evidence
├─ 标题、原始 URL / 文件来源、来源类型、平台、发布者
├─ 采集时间、读取状态、所属竞品、分析维度、可支撑的 Claim 类型
├─ 关键原文片段与原文定位（段落 / 页面 / 章节）
├─ 面向用户的摘要
├─ 规范化正文内容哈希
├─ 可信度总分、分维度分数与风险提示
└─ 来源快照标识
```

**内容哈希与证据版本**

每次成功读取公开网页或附件时，对规范化后的正文计算并保存 `content_hash`，同时保留采集时间。它用于：

- 识别同一 URL 本次内容是否相对上次发生变化。
- 识别不同 URL 是否转载了高度相同的正文，避免重复抽取和重复消耗 token。
- 在内容变化时将旧 Evidence 标记为“需要复查”，并触发重新采集 / 重新评分。
- 在内容未变化时复用已有抽取结果。

`content_hash` 是来源内容版本与去重标识，不是事实真伪判断；哈希变化只说明内容发生变化，不自动说明事实已变化。

**失败与数据缺口**

读取失败、登录墙、404、内容过短或来源不明时，应写入采集记录（Source Attempt），说明 URL、失败原因、时间与风险标记；它不是可支撑 Claim 的有效 Evidence，也不计入可用 Evidence 数量。该记录可解释后续 `data_gap` 的来源。

**Token 默认预算**

P0 默认预算是可调节的保护阈值，不是永久产品规则：每个维度最多 2 个检索查询；每个查询最多保留 5 个候选 URL；每个维度最多实际读取 3 个页面；每页最多向模型提供约 4,000–6,000 个相关字符，并只进行一次结构化抽取。后续以可用 Evidence 数、QA 数据缺口、重复来源比例、token 与耗时评估是否调整。

**Memory、Skill 与 Trace**

- 可读取与来源偏好、采集失败模式相关的 Active Memory；Candidate 仅可面向该专家低权重试用，不能作为事实依据。
- P0 不要求为该专家预置多个 Skill。来源规则、Evidence 结构和评分机制属于系统规则或岗位契约；可重复、经评估验证的采集方法才可后续沉淀为 Skill。
- Trace 至少记录检索查询、候选与实际读取 URL、工具调用结果、内容哈希、关键片段定位、采集失败原因、评分输入和最终 Evidence ID。

### 1.3 证据压缩、路由与 Token 预算

证据压缩与路由是 Evidence Library 和各分析专家之间的共享机制。它不是一个独立专家，也不产生业务结论；P0 中由系统模块执行，并由研究编排专家在计划中调用。

它的目标是：在不破坏可追溯性的前提下，把多名证据采集专家产生的 Evidence 转成每个分析专家可以处理的 Evidence Slice。

**执行链路**

```text
Evidence Candidate
  -> content_hash 去重与版本识别
  -> 规则评分
  -> 维度标签
  -> 专家任务路由
  -> 按 Token 预算拆分 Evidence Slice
  -> 分批进入目标分析专家
```

证据压缩不是把证据总结成不可追溯摘要。每个 Evidence Slice 必须继续保留 Evidence ID、URL / 文件来源、采集时间、关键原文片段、原文定位、评分、风险提示和 `content_hash`。LLM 摘要只能帮助阅读，不能替代原文片段。

**去重与版本识别**

- 同一 URL 内容未变化时，可复用既有抽取结果。
- 不同 URL 的 `content_hash` 或正文高度相似时，应合并为同一主证据或标记为重复来源，避免重复消耗上下文。
- 同一内容重复出现不自动提高可信度；只有来自不同独立来源的相互支持，才计入多源支持。
- 内容发生变化时，旧 Evidence 应标记为需要复查，并触发重新采集 / 重新评分。

**标签与路由**

路由标签用于决定证据送给哪个专家，不是事实结论。P0 标签至少覆盖：

- 产品定位、功能能力、用户流程、产品边界、目标客户。
- 定价套餐、价格限制、计费单位、免费额度。
- 用户体验、公开反馈、争议、痛点。
- 官方来源、第三方来源、用户主动提供来源。
- 风险、冲突、数据缺口。

一条 Evidence 可以进入多个专家的 Evidence Slice。例如定价页既可以进入定价策略专家，也可以进入产品分析专家，因为套餐边界可能反映产品功能边界。

**Token 预算原则**

Verity 默认采用“慢但稳”的专业研究模式。15-20 分钟的完整报告生成时间可以接受，因此系统优先保证证据覆盖、引用稳定和结论可复查，而不是追求一次性最快输出。

单轮 Evidence Slice 的预算按模型上下文窗口反推：

```text
证据可用预算
= 模型上下文窗口
- 系统规则
- 专家行为规则
- 用户任务与编排计划
- 输出结构约束
- Memory / Trace 上下文
- 预留给分析推理和结构化输出的空间
```

P0 默认采用保守比例：

- 单轮总输入不超过模型上下文窗口的约 70%。
- Evidence Slice 不超过单轮上下文的约 40%-50%。
- 至少预留约 25%-30% 给分析推理、引用检查和结构化输出。
- 其余空间用于系统规则、专家契约、用户任务、Memory、Trace 和 Schema。

预算按 token 控制，不按证据条数硬切。证据条数只作为粗略参考，因为一条短公告和一篇长帮助文档的 token 成本可能完全不同。

**超预算处理**

当路由给某专家的相关证据超过单轮预算时，不丢弃证据，而是自动分批：

```text
全部相关 Evidence
  -> 按竞品 / 维度 / 来源类型 / token 成本拆分为多个 Evidence Slice
  -> 目标专家逐批生成局部 Analysis Pack
  -> 合并为总 Analysis Pack
  -> 进入交叉验证与 QA Gate
```

因此，一个专家最终应覆盖全部与其任务相关的 Evidence；只是每轮只接收不会破坏上下文稳定性的 Evidence Slice。若单条 Evidence 过长，只提供关键原文片段和定位，原文全文保留在 Evidence Store，需要时回查。

Trace 至少记录：某专家本次共覆盖多少条 Evidence、拆成几批、每批主题和 token 估算、被降权或延后处理的证据原因，以及最终进入 Claim 的 Evidence ID。

### 1.4 产品分析专家执行契约

产品分析专家属于 L2 策略层。它负责把经过路由的产品相关 Evidence Slice 转化为产品维度的 Claim、对比项、风险和数据缺口。它不是证据采集者，也不是最终报告撰写者。

**分析范围**

- 产品定位：竞品面向什么用户、什么场景、解决什么核心问题。
- 核心功能：哪些能力是产品主能力，哪些只是辅助能力或营销表述。
- 用户流程：公开资料能支持的关键使用路径、入口、转化或完成任务流程。
- 产品边界：产品做什么、不做什么，依赖哪些生态、渠道或外部系统。
- 差异化策略：效率、成本、体验、生态、专业深度或垂直场景上的差异。
- 产品风险：证据不足、宣传与实际能力不一致、来源冲突或 data_gap。

**输入**

- Human Gate 已确认的研究范围和编排专家分配的产品分析任务。
- Evidence Router 输出的产品相关 Evidence Slice。
- Evidence ID、评分、关键原文片段、URL / 文件来源、采集时间、风险提示和 `content_hash`。
- 与产品分析相关的 Active Memory，以及目标对象为产品分析专家的 Candidate Memory 试用提示。

产品分析专家不直接读取全量 Evidence Store。若路由给它的证据很多，它应分批处理所有相关 Evidence Slice，生成多个局部 Product Analysis Pack，再合并为总 Product Analysis Pack。

**输出：Product Analysis Pack**

```text
Product Analysis Pack
├─ 产品维度 Claims
├─ 竞品 / 维度对比项
├─ Claim 与 Evidence ID 绑定
├─ 冲突证据与风险说明
├─ data_gap 与补证建议
└─ 合并批次与覆盖证据统计
```

每个 Claim 至少包含：

- `claim_id`
- `claim_text`
- `claim_status`：`supported`、`weakly_supported`、`conflicted`、`unresolved` 或 `unsupported`
- `evidence_ids`
- `reasoning`
- `risk_notes`
- `data_gap`（如有）

**行为边界**

- 不直接采集网页证据，不自行扩大 Human Gate 已确认范围。
- 不做价格结论；价格结构、套餐、计费单位和敏感度由定价策略专家负责。
- 不分析竞品用户公开反馈的体验好坏；这由用户体验分析专家负责。
- 不撰写最终报告；只输出进入总 Analysis Pack 的结构化素材。
- 不把官网宣传语直接当成事实能力。官网可以证明“竞品如何宣传自己”，但实际能力、效果和用户体验仍需其他可复查证据支持。
- 不用 Memory 支撑事实结论。Memory 只能影响分析方法、关注重点或风险偏好，不能替代 Evidence。

**工具权限**

P0 中，产品分析专家默认不展示外部资料工具授权：

- 公开网页搜索：禁用。
- 公开网页读取：禁用。
- 用户 URL 读取：禁用。
- 代码执行器：禁用。

当证据不足时，它应输出 `data_gap` 或补证建议，由研究编排专家决定是否再次调用证据采集专家；产品分析专家不绕过 Evidence Router 自行补采。

**Memory 与 Skill**

- Active Memory 可影响分析侧重点，例如优先区分“功能宣传”和“可复查的实际能力”。
- Candidate Memory 仅在目标对象为产品分析专家、且本次范围包含产品 / 功能 / 定位分析时低权重试用。
- P0 不要求预置产品分析 Skill。功能边界拆解、产品定位归因、用户路径还原等方法只有在多次任务、QA 返工和用户反馈中被验证有效后，才可沉淀为 Skill 草稿并进入版本治理。

**Trace 要求**

至少记录产品分析覆盖的 Evidence 数量、Evidence Slice 批次数、每批主题、合并过程、引用的 Memory / Skill、输出 Claim 与 Evidence 绑定关系、data_gap、补证建议，以及被降权或未采用证据的原因。

### 1.5 定价策略专家执行契约

定价策略专家属于 L2 策略层。它负责分析竞品如何通过价格、套餐、限制条件和价值包装影响用户决策。它不是价格表转录员，也不直接采集网页证据。

**分析范围**

- 定价结构：免费版、订阅制、按量计费、企业定制、混合模式。
- 套餐边界：不同套餐之间的功能、额度、席位、权限、服务支持差异。
- 计费单位：按用户、团队、token、调用次数、项目、存储、席位或功能模块计费。
- 免费策略：免费额度、试用期、免费版限制、引导付费的触发点。
- 价格门槛：最低付费价格、团队使用成本、企业采购门槛。
- 价格与产品能力关系：价格差异是否对应明确功能升级、规模升级或服务升级。
- 定价风险：价格页不透明、隐藏限制、企业版无公开报价、区域价格差异、历史价格不明。
- 横向可比性：不同竞品价格单位不一致时，必须做归一化说明或明确不可比。

**输入**

- Human Gate 已确认的研究范围和编排专家分配的定价分析任务。
- Evidence Router 输出的定价相关 Evidence Slice。
- 官网定价页、套餐页、帮助中心计费说明、FAQ、API 价格页、销售页、公开价格变更信息等证据。
- Evidence ID、评分、关键原文片段、URL / 文件来源、采集时间、风险提示和 `content_hash`。
- 与定价分析相关的 Active Memory，以及目标对象为定价策略专家的 Candidate Memory 试用提示。

定价策略专家不直接读取全量 Evidence Store。若路由给它的定价证据很多，它应分批处理所有相关 Evidence Slice，生成多个局部 Pricing Analysis Pack，再合并为总 Pricing Analysis Pack。

**输出：Pricing Analysis Pack**

```text
Pricing Analysis Pack
├─ 定价维度 Claims
├─ 竞品 / 套餐 / 计费单位对比矩阵
├─ Claim 与 Evidence ID 绑定
├─ 价格归一化说明
├─ 不可比项、隐藏限制与风险说明
├─ data_gap 与补证建议
└─ 合并批次与覆盖证据统计
```

每个定价 Claim 至少包含：

- `claim_id`
- `claim_text`
- `claim_status`：`supported`、`weakly_supported`、`conflicted`、`unresolved` 或 `unsupported`
- `evidence_ids`
- `billing_unit`（如适用）
- `normalization_note`（如适用）
- `reasoning`
- `risk_notes`
- `data_gap`（如有）

**行为边界**

- 不直接采集网页证据，不自行扩大 Human Gate 已确认范围。
- 不判断产品功能本身强弱；功能边界和产品定位由产品分析专家负责。
- 不分析竞品用户体验好坏；这由用户体验分析专家负责。
- 不撰写最终报告；只输出进入总 Analysis Pack 的结构化素材。
- 不把官网标价直接推断为真实成交价格；企业定制、折扣、地区价格和销售报价必须标注不确定性。
- 不用单一价格点支撑强商业结论。
- 不把不同计费单位的价格粗暴比较为“谁更便宜”；必须先归一化，或明确说明不可比。

**工具权限**

P0 中，定价策略专家默认不展示外部资料工具授权：

- 公开网页搜索：禁用。
- 公开网页读取：禁用。
- 用户 URL 读取：禁用。
- 代码执行器：禁用。

当价格证据不足时，它应输出 `data_gap` 或补证建议，由研究编排专家决定是否再次调用证据采集专家；定价策略专家不绕过 Evidence Router 自行补采。

复杂价格归一化可能需要计算能力，例如 token 单价、调用次数、团队总成本、年付折扣换算。P0 不把代码执行器作为该专家的对外工具；后续可评估受控的“定价计算器”工具，但必须保留公式、输入证据和计算结果 Trace。

**Memory 与 Skill**

- Active Memory 可影响定价分析侧重点，例如比较 API 价格时优先换算到同预算下的 token 可用量、调用次数、上下文长度、速率限制、免费额度和套餐限制。
- Candidate Memory 仅在目标对象为定价策略专家、且本次范围包含定价 / 套餐 / 商业模式分析时低权重试用。
- Memory 不能作为价格证据。价格事实必须来自定价页、官方说明、公开资料或用户主动提供材料。
- P0 不要求预置定价分析 Skill。套餐边界拆解、单位价格归一、API 价格换算、免费额度价值评估、企业版不透明风险检查等方法，只有在多次任务、QA 返工和用户反馈中被验证有效后，才可沉淀为 Skill 草稿并进入版本治理。

**Trace 要求**

至少记录定价分析覆盖的 Evidence 数量、Evidence Slice 批次数、每批主题、使用的归一化口径、引用的 Memory / Skill、输出 Claim 与 Evidence 绑定关系、不可比项、data_gap、补证建议，以及被降权或未采用证据的原因。

### 1.6 用户体验分析专家执行契约

用户体验分析专家属于 L2 策略层。它负责分析竞品终端用户在合法、可复查来源中表达的使用体验、痛点、价值感知、分歧和语义风险。它不是全网舆情采集器，也不是用户心理读心器。

**核心原则**

事实完整性优先于内容丰满度。没有足够用户体验证据时，必须输出 `insufficient_evidence` 或 `not_available`，不能为了让报告显得完整而补故事。用户体验分析专家的空输出不是失败，而是高质量风险控制结果。

**可用来源**

- 用户主动提供的评论页、帖子、评测文章、社区讨论链接、访谈纪要、客服反馈、问卷结果或内部调研材料。
- 公开可访问、无需登录、无需绕过限制的应用商店评价页、插件市场评价页、产品社区帖子或公开评测文章。
- 官网案例中的用户原话可作为“官方筛选案例”证据，但不能等同于自然用户反馈。

**不可承诺**

- 不做全网舆情监控。
- 不绕过登录墙、验证码、反爬或平台访问限制。
- 不大规模抓取社交媒体、论坛或评论区。
- 不把情绪分类当作最终事实。
- 不用单条评论支撑强结论。
- 不把官方客户案例等同于自然用户反馈。

**输入**

- Human Gate 已确认的研究范围和编排专家分配的用户体验分析任务。
- Evidence Router 输出的用户体验相关 Evidence Slice。
- Evidence ID、评分、关键原文片段、URL / 文件来源、采集时间、风险提示和 `content_hash`。
- 与用户体验分析相关的 Active Memory，以及目标对象为用户体验分析专家的 Candidate Memory 试用提示。

该专家只分析已经合法获得并被路由的 Evidence Slice。若没有足够自然用户反馈，不应自行扩大来源范围，应输出证据覆盖不足和补证建议。

**证据覆盖分级**

- `sufficient`：有多个可复查来源，反馈方向相对一致，可形成较稳体验 Claim。
- `limited`：有少量可复查反馈，只能形成弱结论或体验信号，必须标注样本不足。
- `insufficient_evidence`：有零散材料，但不足以支撑体验判断，只输出 data_gap、风险和补证建议。
- `not_available`：没有合法可用的用户体验证据，不输出体验判断。

**语义风险识别**

用户体验分析不能只做 `positive / negative` 情绪分类。每条关键反馈应尽量区分：

- 原文表达。
- 表面情绪。
- 可能真实意图。
- 反讽、玩笑、夸张、语境缺失、翻译或平台语境风险。
- 是否需要人工复核。
- 能否支撑体验 Claim。

例如“呵呵，这个用户体验真是太棒了”不能直接判定为正面反馈，应标注为可能反讽、低置信、需要复核，且不能单独支撑用户满意结论。

**输出：User Experience Analysis Pack**

```text
User Experience Analysis Pack
├─ evidence_coverage
├─ experience_claims
├─ pain_points
├─ perceived_values
├─ disagreements
├─ semantic_risks
├─ sample_limits
├─ data_gaps
└─ 覆盖证据统计
```

当 `evidence_coverage` 为 `insufficient_evidence` 或 `not_available` 时，`experience_claims` 必须为空，报告撰写专家不得强行写出“用户普遍认为……”等体验结论。

每个体验 Claim 至少包含：

- `claim_id`
- `claim_text`
- `claim_status`：`supported`、`weakly_supported`、`conflicted`、`unresolved` 或 `unsupported`
- `evidence_ids`
- `sample_limit`
- `semantic_risk`
- `reasoning`
- `risk_notes`
- `data_gap`（如有）

**行为边界**

- 不直接采集网页证据，不自行扩大 Human Gate 已确认范围。
- 不判断产品功能本身强弱；功能边界和产品定位由产品分析专家负责。
- 不判断价格是否划算；定价结构和价格可比性由定价策略专家负责。
- 不撰写最终报告；只输出进入总 Analysis Pack 的结构化素材。
- 不根据少量、单一来源或语义风险高的反馈输出强结论。
- 不把用户体验反馈当作产品事实本身。用户说“功能不能用”是体验信号，是否真的不可用还需要产品证据或交叉验证。

**工具权限**

P0 中，用户体验分析专家默认不展示外部资料工具授权：

- 公开网页搜索：禁用。
- 公开网页读取：禁用。
- 用户 URL 读取：禁用。
- 代码执行器：禁用。

当用户体验证据不足时，它应输出 `insufficient_evidence`、`not_available` 或补证建议，由研究编排专家决定是否再次调用证据采集专家；该专家不绕过 Evidence Router 自行补采。

**Memory 与 Skill**

- Active Memory 可影响分析侧重点，例如优先标注反讽风险、官方案例偏差或样本不足。
- Candidate Memory 仅在目标对象为用户体验分析专家、且本次范围包含用户体验 / 用户反馈分析时低权重试用。
- Memory 不能作为用户体验事实证据。体验判断必须来自可复查的用户表达、公开材料或用户主动提供材料。
- P0 不要求预置用户体验分析 Skill。反讽识别检查、样本限制评估、官方案例偏差检查等方法，只有在多次任务、QA 返工和用户反馈中被验证有效后，才可沉淀为 Skill 草稿并进入版本治理。

**Trace 要求**

至少记录用户体验分析覆盖的 Evidence 数量、Evidence Slice 批次数、证据覆盖分级、关键语义风险、样本限制、引用的 Memory / Skill、输出 Claim 与 Evidence 绑定关系、data_gap、补证建议，以及因证据不足而未输出结论的原因。

### 1.7 交叉验证专家执行契约

交叉验证专家属于 L2 策略层偏审计角色。它负责检查不同专家输出的 Claim、Evidence、风险和 data_gap 是否能够共同进入同一份报告。它不产生新的业务事实，也不追求让结论更漂亮。

交叉验证专家回答的问题是：

> 这些专家结论能不能同时成立？有没有互相打架、证据错配、强度过高或来源冲突？

**运行实例规则**

交叉验证专家是专家类型，运行时可以拆成多个同类型实例。专家公会只展示“交叉验证专家”这一类；Trace 展示本次实际启动的实例。

P0 默认可按检查范围拆分：

- 产品 Claim 内部一致性检查。
- 定价 Claim 内部一致性检查。
- 用户体验 Claim 内部一致性检查。
- 产品 × 定价冲突检查。
- 产品 × 用户体验冲突检查。
- 定价 × 用户体验冲突检查。
- 汇总交叉验证实例：合并冲突、去重、判断严重程度并输出 Cross Validation Pack。

拆分不是为了堆 Agent 数量。只有竞品数量、Evidence Slice、Claim 数量、分析维度或冲突风险达到阈值时才拆；否则单个交叉验证实例即可。

**输入**

- 各分析专家输出的 Analysis Pack，包括产品、定价、用户体验等维度。
- 每个 Claim 绑定的 Evidence ID、评分、风险、来源类型、采集时间和 `content_hash`。
- Evidence Router 的切片记录、批次、被降权或延后处理的证据原因。
- 专家输出中的 `data_gap`、`semantic_risk`、`normalization_note`、`sample_limit` 等风险字段。
- Human Gate 已确认范围和研究编排计划。

**检查范围**

- Claim 之间是否冲突：例如产品分析说主打企业客户，定价分析却显示公开套餐主要面向个人和小团队。
- Claim 与 Evidence 是否匹配：例如价格结论引用了功能页，用户体验结论引用了官方客户案例却写成自然用户反馈。
- 结论强度是否过高：例如只有低置信证据却标为 `supported`。
- 来源使用是否越界：例如用户评论只能证明用户表达，不能直接证明产品功能事实。
- 跨专家 data_gap 是否重复或相互影响：例如产品和定价都缺企业版证据，应合并为同一个关键风险。
- 不可比项、语义风险、样本限制是否被后续结论正确继承。

**输出：Cross Validation Pack**

```text
Cross Validation Pack
├─ claim_checks
├─ conflicts
├─ evidence_misuse
├─ downgrade_suggestions
├─ merged_data_gaps
├─ rework_suggestions
└─ 覆盖 Claim / Evidence / Pack 统计
```

每个检查项至少包含：

- `check_id`
- `check_scope`
- `affected_claim_ids`
- `related_evidence_ids`
- `issue_type`：`conflict`、`evidence_misuse`、`overclaim`、`source_boundary`、`data_gap` 或 `inconsistency`
- `severity`：`low`、`medium`、`high`
- `suggested_action`：`keep`、`downgrade`、`mark_conflict`、`needs_rework` 或 `report_with_risk`
- `reasoning`

**行为边界**

- 不采集新证据，不自行扩大 Human Gate 已确认范围。
- 不生成新的业务事实或最终报告。
- 不替代 QA Gate 做整体放行；它输出的是一致性审计结果，QA Gate 决定 Analysis Pack 是否可以进入报告阶段。
- 不擅自覆盖其他专家结论，只提出保留、降级、标冲突、返工或带风险进入报告的建议。
- 不无限要求返工；返工仍受 QA Gate 最多 1 次的全局规则约束。
- 不为了消除冲突而强行合并矛盾结论。真实冲突应保留为报告风险或分歧。

**工具权限**

P0 中，交叉验证专家默认不展示外部资料工具授权：

- 公开网页搜索：禁用。
- 公开网页读取：禁用。
- 用户 URL 读取：禁用。
- 代码执行器：禁用。

当发现缺少必要证据时，它只能输出 `data_gap` 或补证建议，由研究编排专家和 QA Gate 决定是否触发返工；交叉验证专家不绕过 Evidence Router 自行补采。

**Memory 与 Skill**

- Active Memory 可影响一致性检查侧重点，例如优先检查官网宣传误用、定价不可比、官方案例被误当自然反馈等已验证问题。
- Candidate Memory 仅在目标对象为交叉验证专家、且与本次检查范围相关时低权重试用。
- Memory 不能作为事实证据，只能影响检查方法和风险关注点。
- P0 不要求预置交叉验证 Skill。Claim-Evidence 错配检查、跨维度冲突检查、过强结论降级检查等方法，只有在多次任务、QA 返工和用户反馈中被验证有效后，才可沉淀为 Skill 草稿并进入版本治理。

**Trace 要求**

至少记录本次启动的交叉验证实例、每个实例的检查范围、覆盖 Claim / Evidence / Pack 数量、发现的冲突与严重程度、降级或返工建议、引用的 Memory / Skill、汇总合并过程，以及未采纳某些冲突建议的原因。

### 1.8 QA 质检专家执行契约

QA 质检专家属于 L2 策略层的出报告前验收角色。它不重新做分析，不采集新证据，也不写最终报告；它判断当前 Analysis Pack 是否达到可以交给报告撰写专家的标准。

QA 质检专家检查的是报告前的 Analysis Pack，而不是等报告写完后做文笔润色。

**输入**

QA 质检专家默认不读取所有专家子 Pack 的全文。它的主输入是 QA Brief：

- QA Brief Builder 输出的结构化风险摘要。
- Cross Validation Pack。
- Human Gate 范围摘要与 Research Plan 摘要。
- 当前 `rework_count`。
- 必要的局部 Claim / Evidence 片段。

QA Brief Builder 是系统模块，不是专家，也不是 LLM 总结器。它通过规则扫描结构化 Pack，抽取 Claim ID、Evidence ID、评分、风险、data_gap、交叉验证问题和处理状态，生成面向 QA Gate 的问题索引。

**检查范围**

- Claim 是否绑定 Evidence，Evidence 是否足够支撑 Claim。
- Claim 状态是否匹配证据质量，例如低置信证据不能支撑 `supported`。
- Cross Validation Pack 中的冲突、降级建议和 data_gap 是否已有处理路径。
- 用户体验维度为 `insufficient_evidence` / `not_available` 时，是否仍存在强体验结论。
- 定价维度是否标注不可比项、隐藏限制、企业版不透明风险和归一化口径。
- 产品维度是否区分官网宣传、可复查产品能力和推断。
- 是否存在无证据 Claim、错引 Evidence、过强结论、遗漏风险提示或范围越界。

**问题处理路径**

QA Gate 不负责亲自解决问题，而是决定每个问题的处理路径：

- `fix_in_pack`：返回原分析专家修正结构化结论。
- `downgrade`：降低 `claim_status` 或结论强度。
- `keep_as_conflict`：保留冲突，并要求报告披露。
- `mark_data_gap`：标记证据缺口，不强行补结论。
- `request_more_evidence`：仅当缺口在当前范围内可补、且返工次数未用完时，才请求证据采集专家补证。
- `need_human_review`：涉及范围变更、关键选择或用户偏好时请求人工确认。
- `pass_with_risk`：当前范围内无法修复，但风险已充分披露时带风险通过。

交叉验证专家和 QA 质检专家发现的问题不默认触发重新采集。多数问题应通过降级、保留冲突、披露风险或标记 data_gap 处理；只有可在已确认范围内补证的问题，才可能进入补证返工。

**输出：QA Gate Result**

```text
QA Gate Result
├─ qa_status
├─ rework_count
├─ scores
├─ hard_failures
├─ issues
├─ issue_handling_paths
├─ target_experts（如需返工）
└─ final_decision_reason
```

`qa_status` 可为：

- `pass`：Analysis Pack 合格，可以进入报告撰写。
- `rework`：存在可修复的高风险问题，且尚未返工过。
- `pass_with_risk`：问题无法在当前范围内修复，或已经返工过但风险可披露。
- `need_human_review`：需要用户确认范围、取舍或是否接受风险。

**行为边界**

- 不采集新证据，不自行扩大 Human Gate 已确认范围。
- 不重新做产品、定价或用户体验分析。
- 不为了让报告通过而替其他专家补结论。
- 不把 QA 意见变成新的事实依据。
- 不允许无限返工；QA Gate 最多触发 1 次返工。
- 不直接读取全量子 Pack；需要细查时按 Claim ID / Evidence ID 局部回查。

**工具权限**

P0 中，QA 质检专家默认不展示外部资料工具授权：

- 公开网页搜索：禁用。
- 公开网页读取：禁用。
- 用户 URL 读取：禁用。
- 代码执行器：禁用。

**Memory 与 Skill**

- Active Memory 可影响 QA 检查重点，例如特别关注用户体验证据不足时的过强结论、官网客户案例误用、定价不可比等问题。
- Candidate Memory 仅在目标对象为 QA 质检专家、且与本次质检范围相关时低权重试用。
- QA 返工中沉淀出的高价值规则可进入 Memory Candidate；多次验证有效后，才可沉淀为 Skill 草稿并进入版本治理。
- Memory 不能作为事实证据，只能影响检查方法和风险关注点。

**Trace 要求**

至少记录 QA Brief 版本、命中的规则、评分、硬门槛失败、问题处理路径、是否触发返工、目标专家、返工前后差异，以及最终 `pass` / `rework` / `pass_with_risk` / `need_human_review` 的原因。

### 1.9 报告撰写专家执行契约

报告撰写专家属于 L1 执行层的表达生成角色。它不发现新事实，不判断结论是否成立，也不采集新证据；它只负责把通过 QA Gate 的 Analysis Pack 写成用户能读懂、能追溯、能看到风险的报告。

报告撰写专家是受约束的表达器，不是自由发挥的分析器。它的创造力只能体现在结构、表达、可读性和引用呈现上，不能体现在新增事实、补充结论或隐藏风险上。

**运行实例规则**

报告撰写专家是专家类型，运行时可以拆成多个同类型写作实例。专家公会只展示“报告撰写专家”这一类；Trace 展示本次实际启动的章节实例和总编实例。

P0 默认采用“章节写作实例 + 总编合并实例”的结构：

```text
QA 通过的 Analysis Pack
  -> 报告大纲
  -> 分章节撰写实例并行
  -> 总编实例统一口径、引用、风险和风格
  -> Report Renderer 生成最终报告产物
```

可拆分的章节实例包括：

- 执行摘要。
- 产品分析章节。
- 定价分析章节。
- 用户体验章节。
- 风险与数据缺口章节。
- 引用与证据索引章节。
- 总编合并实例。

拆分不是为了展示 Agent 数量，而是为了处理长报告、多竞品、多章节和单个上下文放不下的情况。章节实例只读取本章节相关的 Claim、Evidence 引用、风险和输出约束；总编实例读取各章节草稿、QA Gate Result、Cross Validation 高风险项、Claim-Evidence 索引和报告结构约束。

**输入**

- QA Gate 通过后的 Analysis Pack，或 `pass_with_risk` 的 Analysis Pack。
- QA Gate Result。
- Cross Validation Pack 中需要继承到报告的冲突、降级、data_gap 和风险。
- Claim-Evidence 索引、Evidence 引用元信息和必要的局部原文片段。
- Human Gate 已确认范围。
- 报告大纲、章节结构和输出格式约束。
- 可展示的 Decision Trace 摘要。

报告撰写专家不直接读取全量 Evidence 原文。需要引用时，应通过 Claim ID / Evidence ID 使用已通过 QA 的引用索引和必要片段。

**输出：Traceable Report Draft**

```text
Traceable Report Draft
├─ Executive Summary
├─ Scope & Source Boundary
├─ Key Findings
├─ Product Analysis
├─ Pricing Analysis
├─ User Experience Analysis
├─ Cross-validation Notes
├─ Data Gaps & Risks
├─ Evidence References
└─ Decision Trace Summary
```

每个关键结论至少保留：

- `section_id`
- `claim_id`
- `evidence_ids`
- `claim_status`
- `risk_notes`
- `data_gap`（如有）

当 QA Gate Result 为 `pass_with_risk` 时，报告必须在摘要和相关章节中显式披露风险，不能只放在附录或引用列表里。

**总编实例规则**

总编实例负责统一多章节草稿，但不能新增核心结论。它必须检查：

- 所有关键 Claim 是否来自通过 QA 的 Analysis Pack。
- 每个关键结论是否绑定 Evidence ID。
- `unsupported`、`conflicted`、`insufficient_evidence` 或 `not_available` 是否被写成确定结论。
- 执行摘要是否把弱结论写成强结论。
- 风险提示、data_gap、不可比项、样本限制和语义风险是否被继承。
- 引用格式、章节风格和术语是否一致。
- 重复段落和章节之间的矛盾是否被处理。

**Report Renderer**

Report Renderer / Report Artifact Builder 是系统模块，不是报告撰写专家本体。它负责把 Traceable Report Draft 和图表 / 表格规范渲染为 Markdown、HTML、PDF 或前端页面展示。

报告撰写专家不允许调用通用代码执行器做自由计算，但可以调用受控的报告渲染与可视化工具，把已通过 QA 的结构化数据转换成表格、图表和引用索引。

P0 允许展示的具体工具权限：

- 报告渲染器：允许。
- 表格生成器：允许。
- 图表规范生成器：允许。
- 引用索引生成器：允许。
- 公开网页搜索：禁用。
- 公开网页读取：禁用。
- 用户 URL 读取：禁用。
- 通用代码执行器：禁用。

表格和图表必须满足：

- 数据来自通过 QA 的 Analysis Pack、Evidence Metadata 或 Claim-Evidence 索引。
- 图表必须保留数据来源或 Evidence ID。
- 不生成没有数据表支撑的图表。
- 不生成未定义口径的“综合实力”“市场吸引力”“用户满意度趋势”等推断型指标。

可以生成：

- 价格对比表。
- 功能 / 套餐边界对比表。
- Evidence Confidence 分布。
- Claim 状态分布。
- 风险类型统计。
- Evidence 引用索引。

**行为边界**

- 不采集新证据，不自行扩大 Human Gate 已确认范围。
- 不新增 Analysis Pack 中不存在、且没有证据绑定的核心结论。
- 不把 `unsupported` / `conflicted` Claim 写成确定结论。
- 不把用户体验 `insufficient_evidence` / `not_available` 写成“用户普遍认为”。
- 不把官网宣传写成已验证事实。
- 不隐藏 data_gap、QA 风险、不可比项或样本限制。
- 不为了报告完整性编造趋势、图表、数据或结论。

**Memory 与 Skill**

- Active Memory 可影响表达偏好，例如风险提示优先展示、价格归一化说明位置、引用展示格式。
- Candidate Memory 仅在目标对象为报告撰写专家、且与本次报告表达相关时低权重试用。
- Memory 不能作为事实证据，不能让报告新增 Analysis Pack 外的核心结论。
- P0 不要求预置大量写作 Skill。报告结构优化、风险提示表达、引用展示格式等方法，只有在多次任务、QA 返工和用户反馈中被验证有效后，才可沉淀为 Skill 草稿并进入版本治理。

**Trace 要求**

至少记录报告大纲、启动的章节写作实例、每个实例的输入 Claim 范围、总编合并过程、被删除或降级的表述、使用的渲染工具、生成的表格 / 图表规范、引用索引，以及最终报告章节与 Claim / Evidence 的映射关系。

## 2. Evidence Scoring

### 2.1 产品定义

Evidence Confidence 是证据质量评分。它评估的是：

> 这条证据对当前分析任务是否可靠、相关、可复查、信息充分。

它不等同于“事实真伪绝对判定”。

### 2.2 分数与阈值

总分范围：`0-100`

| 等级 | 分数 | 含义 |
| --- | ---: | --- |
| 高可信 | `80-100` | 可作为关键结论的主要支撑，但仍需保留来源和风险说明 |
| 中可信 | `50-79` | 可作为辅助支撑或趋势提示，强结论需要多源验证 |
| 低可信 | `<50` | 不应支撑强结论，只能作为风险、线索或数据缺口提示 |

### 2.3 评分维度

Evidence Confidence 由 6 个正向维度和 1 个风险扣分项组成。

```text
confidence =
  source_authority
  + relevance
  + verifiability
  + freshness
  + specificity
  + corroboration
  - risk_penalty
```

| 维度 | 权重 | 说明 |
| --- | ---: | --- |
| `source_authority` | 20 | 来源对当前 claim 是否有一手解释权 |
| `relevance` | 20 | 是否直接相关于当前竞品、任务和分析维度 |
| `verifiability` | 15 | 是否可复查、可打开、元信息是否充分 |
| `freshness` | 10 | 是否足够新，是否可能过期 |
| `specificity` | 15 | 是否有具体功能、价格、数据、案例或用户原话 |
| `corroboration` | 10 | 是否被其他独立证据支持，是否存在冲突 |
| `risk_penalty` | 0-10 | 抓取失败、登录墙、广告页、内容过短等风险扣分 |

### 2.4 来源权威性 `source_authority`

来源权威性不是“官网永远 20 分，评论永远低分”。它取决于该来源是否对当前 claim 有一手解释权。

| 分数 | 规则 |
| ---: | --- |
| 18-20 | 对当前 claim 有一手解释权，例如官网、官方文档、财报、定价页、产品帮助中心、官方公告 |
| 14-17 | 权威二手来源，例如主流媒体、研究机构、行业报告、可信数据库 |
| 10-13 | 专业但非官方来源，例如专家博客、开发者评测、垂直媒体、公开演讲整理 |
| 5-9 | 普通网页、论坛、社区帖子、用户评论、社媒内容 |
| 0-4 | 来源不明、聚合页、转载来源不清、疑似广告页 |

按 claim 类型微调：

| Claim 类型 | 高权威来源示例 |
| --- | --- |
| `pricing` | 官网定价页、官方帮助中心、销售文档、财报 |
| `feature` | 官方产品页、文档、release notes、帮助中心 |
| `positioning` | 官网首页、官方博客、发布会、创始人访谈 |
| `user_voice` | 用户访谈、公开评论、社区讨论、评价平台；需要多源交叉验证 |
| `market` | 财报、行业报告、研究机构、权威媒体 |
| `business_model` | 官网套餐、财报、招聘/渠道信息、公开商业分析 |

### 2.5 相关性 `relevance`

| 分数 | 规则 |
| ---: | --- |
| 18-20 | 直接讨论目标竞品和当前分析维度 |
| 12-17 | 讨论目标竞品，但与当前维度相关性不完整 |
| 6-11 | 只讨论相同行业、相似场景或间接信息 |
| 0-5 | 与当前竞品或分析任务基本无关 |

### 2.6 可复查性 `verifiability`

| 分数 | 规则 |
| ---: | --- |
| 13-15 | 有 URL 或文件来源，可打开，有标题、来源平台、发布时间或作者等元信息 |
| 9-12 | 有 URL 或文件来源，可打开，但元信息不完整 |
| 4-8 | 只有截图、摘要、二手转述或不可直接验证来源 |
| 0-3 | 无法打开、抓取失败、来源缺失 |

### 2.7 时效性 `freshness`

| 分数 | 规则 |
| ---: | --- |
| 9-10 | 近 6 个月，或明确仍然有效 |
| 6-8 | 6-18 个月，可能仍可参考 |
| 3-5 | 18-36 个月，仅适合历史背景 |
| 0-2 | 超过 36 个月、无时间信息、或明显过期 |

定价、功能、用户反馈类证据对时效更敏感；公司定位、长期战略、历史演进类证据可适当放宽。

### 2.8 信息具体性 `specificity`

| 分数 | 规则 |
| ---: | --- |
| 13-15 | 包含具体价格、功能、数据、案例、用户原话、版本变化或明确事实 |
| 9-12 | 有明确描述，但缺少数据或细节 |
| 4-8 | 泛泛而谈，信息密度较低 |
| 0-3 | 文本过短、空泛、营销话术堆叠，缺少可用信息 |

### 2.9 多源支持 `corroboration`

| 分数 | 规则 |
| ---: | --- |
| 8-10 | 被 2 条以上独立证据支持，且无明显冲突 |
| 5-7 | 有 1 条辅助证据支持 |
| 2-4 | 单一来源，暂未交叉验证 |
| 0-1 | 与其他证据存在明显冲突，或只有低可信来源支持 |

### 2.10 风险扣分 `risk_penalty`

风险扣分范围：`0-10`

| 风险 | 建议扣分 |
| --- | ---: |
| 抓取失败、页面无法打开、404 | 5-10 |
| 登录墙、付费墙、只抓到摘要 | 3-6 |
| 内容过短，无法支撑判断 | 2-5 |
| 疑似广告页、聚合页、SEO 农场 | 3-6 |
| 来源时间明显过期 | 2-5 |
| 与其他证据存在冲突 | 3-8 |
| 来源不明或转载链条不清 | 3-6 |

### 2.11 规则评分与 LLM 的边界

P0 采用规则评分为主，LLM 辅助摘要、解释、风险提示和相关性判断。

LLM 不应单独决定最终可信度分数。它可以输出：

- `evidence_summary`
- `risk_note`
- `relevance_rationale`
- `suggested_claim_usage`

但最终分数必须能追溯到规则维度。

P2 实现口径：

- 可信度总分由规则函数计算，LLM 不直接写入最终分数。
- LLM 可以帮助判断文本相关性、摘要、风险解释，但这些内容必须落回可解释字段。
- API 保存总分、等级、各维度分、风险扣分和风险提示。
- UI 展示总分时必须能解释分数来源，不能只展示一个孤立数字。
- 低可信证据不得用于支撑强结论；中可信证据支撑强结论时必须有多源交叉验证。
- 抓取失败、无法打开、样本不足、来源不明、明显过期等风险必须进入 `risk_penalty` 或 `risk_note`。

### 2.12 Evidence 数据结构

P0 推荐字段：

```json
{
  "id": "ev_001",
  "title": "GitHub Copilot Pricing",
  "url": "https://github.com/features/copilot/plans",
  "source_type": "official",
  "platform": "github",
  "captured_at": "2026-07-09",
  "content_hash": "sha256:...",
  "retrieval_status": "success",
  "claim_types": ["pricing"],
  "scores": {
    "source_authority": 20,
    "relevance": 19,
    "verifiability": 14,
    "freshness": 9,
    "specificity": 13,
    "corroboration": 8,
    "risk_penalty": 2
  },
  "confidence": 81,
  "confidence_level": "high",
  "summary": "官方定价页，适合用于 Copilot 价格和套餐对比。",
  "risk_note": "价格可能随地区或时间变化，需要定期刷新。"
}
```

`content_hash` 对应采集时的规范化正文版本，用于来源去重、复用和页面更新后的复查，不参与 Evidence Confidence 的事实真伪判断。

## 3. Claim-Evidence Binding

证据库不是链接集合。Verity 必须展示每条证据支撑了哪个结论。

### 3.1 Claim 状态

| 状态 | 含义 |
| --- | --- |
| `supported` | 有足够证据支撑，可进入报告核心结论 |
| `weakly_supported` | 有证据但不充分，需要保守表达 |
| `conflicted` | 证据之间存在冲突，需要标注争议 |
| `unresolved` | 数据缺口未解决，不能强行下结论 |
| `unsupported` | 缺少证据，不应进入报告核心结论 |

### 3.2 Claim 使用规则

- 强结论必须绑定至少 1 条高可信证据，或多条中可信证据交叉支持。
- 用户声音类结论不应只依赖单条评论或单一社媒内容。
- 低可信证据只能作为风险提示、线索或待验证假设。
- Report Writer 不得新增 Analysis Pack 中不存在、且没有证据绑定的核心结论。

## 4. Analysis Pack

Analysis Pack 是报告生成前的结构化素材包。

建议包含：

```json
{
  "report_id": "report_001",
  "research_goal": "...",
  "competitor_schema": {},
  "claims": [],
  "evidence_items": [],
  "claim_evidence_map": [],
  "data_gaps": [],
  "conflicts": [],
  "confidence_summary": {},
  "ready_for_qa": true
}
```

Analysis Pack 的价值：

- 把 Evidence 转换为可质检的 Claim。
- 在报告生成前识别弱证据、冲突和数据缺口。
- 限制 Report Writer 的自由发挥，避免“看似完整但不可追溯”的报告。

P2 实现口径：

- Analysis Pack 不是最终报告，而是报告前的质检对象。
- 每个 Claim 必须显式记录状态、强弱、所属维度和绑定证据。
- `claim_evidence_map` 必须能说明每个结论绑定了哪些证据、最高证据分数和证据等级。
- 未覆盖的用户确认维度会进入 `data_gaps`，不得在报告中被静默补齐。
- `conflicted` / `unsupported` claim 可以保留在 Pack 中，但必须被 QA Gate 识别，不能作为确定性结论写入报告。
- 第一版可以先使用规则函数组装 Pack；LLM 后续只负责辅助生成候选 Claim，不能绕过证据绑定。

## 5. QA Gate

### 5.1 产品定位

QA Gate 检查的是 Analysis Pack 是否足以进入报告撰写，不是检查最终报告文笔。

QA Gate 的输入不是全量专家子 Pack，而是 QA Brief、Cross Validation Pack、范围摘要、返工状态和必要的局部 Claim / Evidence 片段。

### 5.2 QA Brief Builder

QA Brief Builder 是 QA Gate 前的系统模块，不是专家，也不是 LLM 总结器。它不把所有材料塞给模型做摘要，而是从结构化 Analysis Pack、Cross Validation Pack 和 Evidence Metadata 中做规则化抽取、统计和风险排序。

QA Brief Builder 的压缩对象是结构化风险，不是自然语言全文。

默认抽取字段：

- `claim_id`、`claim_text`、`claim_status`、`dimension`
- `evidence_ids`、Evidence 最高 / 最低 / 平均置信度、来源类型
- `risk_notes`、`data_gap`、`semantic_risk`、`sample_limit`、`normalization_note`
- Cross Validation issue ID、严重度、建议动作、处理状态
- Human Gate 范围匹配状态

默认风险规则：

- 找出无证据 Claim。
- 找出强结论只绑定低置信证据的 Claim。
- 找出来源越界、错引 Evidence 或无法追溯的 Claim。
- 找出用户体验 `insufficient_evidence` / `not_available` 但仍输出强体验结论的情况。
- 找出定价不可比但仍做强比较的情况。
- 找出 Human Gate 范围外结论。
- 找出未处理的高严重度交叉验证问题和 data_gap。

QA Brief 默认只保留问题索引、统计和少量必要证据片段。正常低风险 Claim 只保留统计，不展开全文；需要细查时再按 Claim ID / Evidence ID 局部回查。

### 5.3 评分维度

| 维度 | 建议权重 | 检查内容 |
| --- | ---: | --- |
| `evidence_sufficiency` | 25 | 关键 claim 是否有足够证据支持 |
| `dimension_coverage` | 15 | 是否覆盖用户确认的分析维度 |
| `claim_reliability` | 20 | 强结论是否由高/中可信证据支撑 |
| `structured_completeness` | 15 | Analysis Pack 结构是否完整 |
| `evidence_consistency` | 15 | 是否识别并处理证据冲突 |
| `data_gap_risk` | 10 | 数据缺口是否被显式标注 |

### 5.4 Verdict 规则

采用“分数 + 硬门槛”混合。

- `pass`：总分 `>= 75`，且没有硬门槛失败。
- `rework`：存在可修复的高风险问题，且 `rework_count = 0`。
- `pass_with_risk`：问题无法在当前范围内修复，或已经返工过但风险可披露。
- `need_human_review`：需要用户确认范围、取舍或是否接受风险。

硬门槛失败包括：

- 关键 claim 没有证据绑定。
- 强结论只由低可信证据支撑。
- `unsupported` / `conflicted` claim 被当作确定结论。
- 用户确认的核心分析维度缺失。
- 数据缺口存在但未展示。
- Evidence / Claim / Analysis Pack 结构字段缺失，导致无法追溯。

### 5.5 问题处理与返工规则

- P0 / MVP 默认最多返工 1 次。
- 第一次不通过：QA Gate 输出问题、处理路径和目标专家，由研究编排专家生成修订计划。
- 返工后仍不通过：只能 `pass_with_risk` 或 `need_human_review`，不能无限循环。
- 所有返工必须进入 Decision Trace。

QA 问题的处理路径包括：

- `fix_in_pack`：返回原分析专家修正结构化结论。
- `downgrade`：降低 `claim_status` 或结论强度。
- `keep_as_conflict`：保留冲突，并要求报告披露。
- `mark_data_gap`：标记证据缺口，不强行补结论。
- `request_more_evidence`：仅当缺口在当前范围内可补、且返工次数未用完时，才请求证据采集专家补证。
- `need_human_review`：请求用户确认范围、取舍或是否接受风险。
- `pass_with_risk`：带风险进入报告撰写。

交叉验证和 QA 发现的问题不默认触发重新采集。多数问题应通过降级、保留冲突、披露风险或标记 data_gap 处理。

P2 实现口径：

- QA Gate 使用“加权评分 + 硬门槛”。
- 评分维度仍保留 6 项：证据充分性、维度完整性、结论可信度、结构化完整度、证据一致性、数据缺口风险。
- 总分 `>= 75` 且无硬门槛失败才允许 `pass`。
- 触发硬门槛时，即使总分看起来不低，也不能直接进入报告撰写；根据返工次数和风险可处理性进入 `rework`、`pass_with_risk` 或 `need_human_review`。
- `rework_count` 最大为 1；再次失败时，应生成带风险提示的报告，或请求人工确认。

### 5.6 QA Gate 输出结构

```json
{
  "qa_status": "rework",
  "total_score": 68,
  "scores": {
    "evidence_sufficiency": 62,
    "dimension_coverage": 80,
    "claim_reliability": 58,
    "structured_completeness": 76,
    "evidence_consistency": 70,
    "data_gap_risk": 60
  },
  "hard_failures": [
    "strong_claim_supported_only_by_low_confidence_evidence"
  ],
  "issues": [
    "用户声音章节有 2 个强结论只绑定单一低可信样本。"
  ],
  "issue_handling_paths": [
    {
      "issue_id": "qa_001",
      "path": "downgrade",
      "target_experts": ["用户体验分析专家"],
      "reason": "当前证据不足以支撑强体验结论"
    }
  ],
  "rework_count": 0,
  "final_decision_reason": "存在可修复的高风险过强结论，触发一次返工"
}
```

## 6. Research Memory

### 6.1 Memory 与资产的区别

| 类型 | 作用 | 是否影响后续 Agent |
| --- | --- | --- |
| Evidence Library | 保存外部采集证据 | 否，除非被转化为可召回策略 |
| Knowledge Base | 保存用户主动收藏、标注、批注内容 | 否，默认只是资产 |
| Historical Reports | 保存历史研究成果 | 否，默认只是研究资产 |
| Research Memory | 沉淀会让下一次研究质量变好的执行经验，并影响后续 Agent 判断、采集、分析、质检或表达 | 是 |

### 6.2 candidate 与 active

`candidate memory` 是候选记忆：系统从用户反馈、QA 返工、交叉验证或执行复盘中识别出的潜在经验。它不会作为硬规则、事实依据或全局策略影响后续 Agent；与当前任务匹配时，可以仅向目标专家低权重试用。

`active memory` 是生效记忆：会在后续任务中被召回，并影响 Agent 行为。

| 状态 | 含义 | 是否影响后续 Agent |
| --- | --- | --- |
| `candidate` / `draft` | 待确认、待验证的候选记忆 | 仅可向目标专家低权重试用，不是硬规则 |
| `active` | 已通过规则或用户确认，后续可召回 | 是 |
| `quarantined` | 存在风险、冲突、低置信或过期问题 | 否 |
| `archived` | 不再使用，仅保留记录 | 否 |

### 6.3 P3.4 策略

P3.4 先做 memory candidate 和状态治理，不默认自动写入 active memory。

核心原则：

- Memory 不从 Evidence 自动生成；高可信证据仍然只是证据。
- Memory 不从所有 supported claim 自动生成；报告结论默认留在报告资产中。
- Memory 不是保存“有价值的信息”，而是保存“会改变下一次 Agent 行为的少量经验”。
- 每条 Memory 必须声明“作用对象”和“生效策略”，否则只应进入知识库、证据库、历史报告或批注。
- 每份报告自动生成的 Memory Candidate 应严格限量，避免上下文膨胀和记忆污染。

允许进入 candidate 的内容：

- 用户在报告批注中指出分析方法缺口，例如“价格和 token 用量之间是什么关系？”
- 用户在调研范围、设置或批注中表达长期偏好，例如“以后定价分析都要看套餐边界”。
- QA Gate 或 Cross-validation 发现可复用的错误模式，例如“用户声音单源支撑强结论”。
- 某个专家 Agent 的输出被返工后形成明确、可执行的改进规则。

允许进入 active 的条件：

- 用户确认该经验应影响后续类似研究。
- 该经验是偏好、报告风格、专家 checklist 或 QA 标准，而不是未经治理的事实判断。
- 该经验有明确目标 Agent 或影响环节。
- 不含敏感信息，不依赖低可信、冲突或过期内容。

不得进入 active 的内容：

- 低置信结论。
- 冲突未解决的判断。
- 单一来源强推断。
- 临时上下文。
- 敏感信息。
- 过期或不可复查信息。
- 只描述某次报告事实、价格、功能或排名，但不会改变后续执行方式的内容。

### 6.4 反馈驱动的进化链路

Verity 的 Memory 不是让用户输入“记住这点”。用户应通过自然操作表达反馈，系统再判断是否形成 Memory Candidate。

典型链路：

```text
用户批注 / QA 返工 / 交叉验证发现问题
  -> 识别为分析方法缺口或可复用经验
  -> 生成 Memory Candidate
  -> 用户确认或规则治理后进入 active
  -> 影响目标 Agent 的 checklist / prompt / skill / QA 标准
  -> 下一次执行质量提升
```

例子：

用户在大模型价格分析报告中批注：

> 价格和 token 之间是什么关系？同样价格下，哪个大模型 API 可调用次数最多？

这条批注不应沉淀为“某模型价格是多少”的事实记忆，而应沉淀为 Business / Pricing Analyst 的分析经验：

> 大模型价格分析不能只比较订阅价格或 API 标价，还必须比较同预算下的 token 可用量、调用次数、上下文长度、速率限制、免费额度和套餐限制。

这条经验后续应影响：

- Pricing Agent 的分析 checklist。
- Research Orchestrator 的任务拆解。
- QA Gate 对定价章节的检查标准。

### 6.5 Knowledge、Candidate Trial 与长期记忆

用户知识库不是 Research Memory，但知识库中的内容可以作为专家 Agent 的内部资料源。

典型链路：

```text
用户高亮 / 收藏 / 加入知识库
  -> Knowledge Item
  -> 专家 Agent 在研究中检索知识库
  -> 命中内容转为本次报告 Evidence
  -> 报告右侧证据栏展示 source_type = user_knowledge
  -> 用户保留 / 删除 / 标注不合适
  -> 更新 Memory Candidate 的正负信号
```

规则：

- 知识库内容默认只是资料资产，不直接影响 Agent 行为。
- 被专家引用后，知识库内容可成为本次报告 evidence。
- 用户未删除引用只能作为正向信号，不能自动转为 active memory。
- 用户删除、批注“不合适”或 QA 判定不适用时，相关 candidate 应降权或进入 `quarantined`。
- 只有能抽象为执行经验、专家 checklist、报告风格或 QA 标准的内容，才可以进入 Memory Candidate。

Candidate Trial：

- candidate 可以被低权重试用，作为 `candidate_suggestions` 提醒专家。
- candidate trial 不能作为事实依据，也不能支撑强结论。
- active memory 才能进入专家 checklist、prompt 或 skill。
- 每次 trial 必须记录使用次数和后续反馈，避免候选记忆长期悬空。

### 6.6 Memory 类型

P3.4 第一版优先实现：

- `user_preference`：用户长期偏好，例如关注维度、风险提示偏好、报告取向。
- `expert_lesson`：某个专家 Agent 因用户反馈、QA 返工或交叉验证学到的可执行改进规则。
- `report_style`：报告表达偏好，例如证据优先、先结论后证据、显式列出数据缺口。

暂缓自动生成，仅预留类型：

- `research_pattern`：必须有明确复用信号，不能用“拆解成功”这种难以客观评价的概念自动生成。
- `competitor_fact`：不能保存所有事实，只能保存稳定、跨任务复用、带证据和过期策略的背景事实。
- `validated_insight`：不能等同于 supported claim，只能保存能改变后续研究方法的抽象洞察。

### 6.7 Memory 影响点

active memory 必须至少影响以下一种行为：

- 任务理解。
- 专家选择。
- 证据采集策略。
- QA Gate 标准。
- 报告风格。
- 风险判断。

如果一条“记忆”不会影响任何后续行为，它不应被称为 Research Memory。

P3.4 第一版优先实现最小影响点：

- active `expert_lesson` 影响目标专家的 checklist。
- active `user_preference` 影响专家选择或研究重点。
- active `report_style` 影响 Report Writer 的输出风格 metadata。

### 6.8 长期记忆防爆上下文规则

Verity 的 Research Memory 主要是跨任务长期记忆，不是单次 session 内的短期上下文。长期记忆必须限制召回，避免污染上下文。

上下文分层：

```text
Session Context：当前任务短期状态、scope、trace、analysis pack、当前 evidence
Evidence / Knowledge Retrieval：公开证据、用户知识库、上传资料，按需检索
Memory Candidate：可试用经验，低权重提示
Active Research Memory：少量长期经验，稳定影响后续 Agent
```

召回规则：

- 按 `target_agent` 召回；不要把所有 active memory 塞给所有专家。
- 按当前任务相关性召回；与任务无关的长期记忆不进入上下文。
- 第一版限制每个 Agent 最多召回 3 条 active memory。
- 第一版限制每个 Agent 最多试用 2 条 candidate memory。
- 只传经验摘要、影响目标和来源 ID，不传长篇知识库原文。
- Knowledge 不常驻上下文，只在专家需要采集证据时检索。
- active memory 必须支持降权、隔离、归档或回滚。

## 7. Decision Trace

P0 Trace 展示用户可理解、已脱敏、可审计的关键步骤。

每个 TraceStep 尽量包含：

- `stage`
- `expert`
- `task`
- `model`
- `prompt`
- `input`
- `output`
- `token_input`
- `token_output`
- `duration_seconds`
- `status`
- `related_evidence_ids`
- `related_report_sections`

展示前必须脱敏：

- API Key。
- Cookie。
- Authorization header。
- 私密文件路径。
- 敏感用户输入。
- 其他凭据。

## 8. 面试解释要点

可以这样解释 Verity 的核心机制：

> Verity 不是直接让 LLM 写竞品报告，而是先构建证据库，对证据做规则化质量评分，再把证据绑定到 claim，形成 Analysis Pack。QA Gate 在报告生成前检查证据充分性、结论可信度和数据缺口。Report Writer 只能基于通过质检的 Analysis Pack 写报告。最后，Decision Trace 解释 Agent 为什么这么做，Research Memory 只沉淀会影响下一次任务的高质量经验。

最重要的边界：

- 不把 Evidence Confidence 说成事实真伪判定。
- 不把 Mock 数据包装成真实抓取。
- 不把知识库、历史报告、证据库直接等同于 Memory。
- 不让低可信证据支撑强结论。
- 不把原始日志直接当用户可读 Trace。
