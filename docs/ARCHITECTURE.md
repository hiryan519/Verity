# AI Product Research Agent Console Architecture

版本：v0.1  
状态：P0 技术栈与核心机制已确认，待工程实现  
关联文档：`docs/AI_Product_Research_Agent_PRD.md`、`docs/PRD.md`、`docs/MECHANISM.md`

## 1. 架构定位

本项目不是重写 Evolva，也不是从零搭建 Agent Runtime。

架构目标是：

- 复用 Evolva 的 Agent Infra 能力。
- 在其上增加面向竞品研究业务的 Web 产品层。
- 把 Agent 执行过程转译为产品经理可理解的工作流、证据链、Trace、质检和报告资产。

推荐架构：

```text
Next.js Web Frontend
  -> Python FastAPI Adapter Layer
  -> Product Workflow Service
  -> Evolva Agent Infra
  -> SQLite / Local Files
```

P0 技术选择：

- 前端：Next.js + React + Tailwind。
- 后端 / Adapter：Python FastAPI。
- 存储：SQLite。
- Evolva 接入：通过 Adapter / wrapper 复用 Evolva Workflow、Trace、Memory、Skills 和 Tools，不深改 Evolva 底层。
- 数据源模式：`mock`、`local-db`、`evolva` 三层逐步切换。

## 2. 分层设计

### 2.1 Web Frontend

职责：

- 工作台首页和调研范围确认。
- 调研执行页。
- 报告阅读页。
- 决策链路页。
- 我的调研。
- 知识库。
- 专家公会。
- 竞争情报中心。
- 知识图谱。

前端不直接实现 Agent 决策逻辑，只消费后端提供的结构化数据。

P0 使用 Next.js + React + Tailwind 实现页面、路由和视觉系统。UI 开发必须读取 `docs/DESIGN.md`。

### 2.2 API / Adapter Layer

职责：

- 接收 Web 请求。
- 调用 Evolva 或本地 Workflow Service。
- 将 Evolva 的 trace、memory、skill、tool event 转换为产品侧数据结构。
- 对外暴露报告、证据、Trace、专家、记忆等接口。

MVP 建议优先使用轻量 Adapter，避免大改 Evolva 底层。

P0 采用 Python FastAPI 作为 Adapter。原因是 Evolva 本体为 Python 项目，后续接入 Workflow、Trace、Memory、Skills 和 Tools 更直接。前后端分离会增加一个本地服务，但能降低后续接 Evolva 的适配成本。

### 2.3 Product Workflow Service

职责：

- 管理竞品研究业务流程。
- 生成专家任务。
- 执行证据采集。
- 生成 Analysis Pack。
- 执行 QA Gate。
- 触发报告生成。
- 写入报告、证据、claim、trace、memory。

该层是本项目最核心的业务层。

### 2.4 Evolva Agent Infra

优先复用或参考：

- Loop / Workflow。
- Tools。
- Trace。
- Eval / Gate 思路。
- Memory。
- Skills。
- Guardrails / Sandbox。

不要为了业务页面展示直接修改 Evolva 底层核心逻辑。若必须扩展，优先通过 Adapter 或 wrapper 完成。

### 2.5 Storage

MVP 推荐使用 SQLite。

原因：

- 比 JSON 文件更适合报告、证据、结论、引用关系查询。
- 方便支持我的调研、全局证据库、情报中心和知识图谱。
- 本地单用户场景足够轻量。

数据源边界：

- `mock`：用于 UI 与流程预览，必须显式标识。
- `local-db`：SQLite 中的结构化业务数据。
- `evolva`：后续真实 Agent Workflow / Trace / Memory 接入。

## 3. 核心模块

### 3.1 Research Task

负责保存用户输入和调研范围确认结果。

关键字段：

- 原始需求。
- 研究对象。
- 所属领域。
- 候选竞品。
- 分析维度。
- 报告视角。
- 目标市场。
- 目标用户。
- 时间范围。
- 补充说明。

### 3.2 Expert Agent Library

专家是可被主控 workflow 调度的任务型 Agent，而不是单纯的 Skill 或角色 Prompt。

```text
Expert Agent = Role + Goal + Tool Scope + State + Output Schema + Trace
```

Skill 退回为专家 Agent 可调用的方法、知识、Prompt 片段或工具使用规范。

专家 Agent 配置应包含：

- 名称。
- 层级：decision / strategy / execution。
- 职责。
- 系统 Prompt。
- 适用任务。
- 可用工具范围。
- 运行状态。
- 输出 Schema。
- 质量要求。
- Trace 字段。

MVP 核心专家：

- Evidence Collector。
- Product Analyst。
- Business Analyst。
- User Voice Analyst。
- Evidence Reviewer。
- Report Writer。

### 3.3 Parallel Expert Group

用途：

- 并发执行互不依赖的只读专家 Agent 任务。
- 降低等待时间。
- 保持多视角分析。

边界：

- 只读研究、摘要、分析任务可并行。
- 文件写入、Shell、高风险工具、共享状态修改不应默认并行。
- 并行结果必须进入统一汇总和质检。

### 3.4 Evidence Library

证据库保存 Agent 采集到的外部证据，不等同于知识库。

每条证据至少包含：

- 标题。
- URL 或文件来源。
- 来源类型。
- 平台。
- 摘要。
- 抓取时间。
- 可信度总分。
- 维度分数。
- 风险提示。
- 关联竞品。
- 关联 claim。

证据可信度采用规则评分 + LLM 辅助解释，不允许只用一句“官网 90 分、评论 50 分”。具体评分维度、阈值和风险扣分规则以 `docs/MECHANISM.md` 为准。

### 3.5 Claim / Analysis Pack

Analysis Pack 是报告生成前的结构化素材包。

它包含：

- 竞品知识 Schema。
- 结构化论点。
- claim-evidence 绑定关系。
- 置信度。
- 数据缺口。
- 冲突和风险。

Report Writer 只能基于 Analysis Pack 写报告，不应新增未经证据审查的核心结论。

### 3.6 QA Gate

QA Gate 检查 Analysis Pack 是否足以进入报告撰写。

评分维度初版：

- 证据充分性。
- 维度完整性。
- 结论可信度。
- 结构化完整度。
- 证据一致性。
- 数据缺口风险。

输出：

- verdict：pass / rework。
- scores。
- issues。
- recommendations。
- rework_count。

返工最多 1 次。

QA Gate 的评分维度、pass / rework 阈值、硬门槛和返工策略以 `docs/MECHANISM.md` 为准。

### 3.7 Report Renderer

报告不是纯长文，而是可交互研究档案。

报告页需要支持：

- 左侧目录。
- 中间正文。
- 右侧证据 / 标注 / 知识库。
- 引用点击定位。
- 图表与数据表绑定。
- CSV 导出。
- 段落编辑。
- 标注、批注、加入知识库。

### 3.8 Decision Trace

Decision Trace 是面向用户的 Agent Trace 回放，不是底层调试日志原样展示。

需要将 Evolva trace event 映射为产品阶段：

- 需求理解。
- 编排派遣。
- 证据采集。
- 交叉分析。
- 报告撰写。
- 质检审查。
- 签发交付。

单步 Trace 应包含：

- stage。
- expert。
- task。
- model。
- prompt。
- input。
- output。
- token_input。
- token_output。
- duration。
- status。
- related_evidence_ids。
- related_report_sections。

展示前必须脱敏密钥、Cookie、API Key 等敏感信息。

### 3.9 Research Memory

历史报告、知识库、证据库不等于 Agent Memory。

真正的记忆必须影响后续执行：

- 任务理解。
- 专家选择。
- 证据采集策略。
- 质检标准。
- 报告风格。
- 风险判断。

Research Memory 类型初版：

- user_preference。
- research_pattern。
- competitor_fact。
- validated_insight。
- expert_lesson。
- report_style。

写入 active memory 前需要考虑置信度、证据、状态、过期和人工确认。

P0 默认先写入 memory candidate，不自动进入 active memory。candidate / active 的区别、状态流转和影响点以 `docs/MECHANISM.md` 为准。

记忆系统偏轻量时，不能再把多 Agent 编排弱化为 Skill 调用。专家 Agent 的并行执行、独立 Trace、任务状态和结构化输出，是本项目体现 Agent 产品能力的核心部分。

## 4. 数据模型

### 4.1 reports

- id
- title
- research_goal
- competitors
- status
- created_at
- updated_at
- evidence_count
- claim_count
- qa_status
- trace_run_id

### 4.2 expert_agents

- id
- name
- layer
- role_description
- system_prompt
- tool_scope
- output_schema
- applicable_tasks
- quality_rules


### 4.3 evidence_items

- id
- report_id
- title
- url
- source_type
- platform
- captured_at
- summary
- confidence
- relevance
- reliability
- freshness
- specificity
- cross_source_support
- risk_penalty
- risk_note
- raw_text

### 4.4 claims

- id
- report_id
- claim_text
- claim_type
- competitor
- confidence
- status
- evidence_ids
- risk_note

### 4.5 analysis_packs

- id
- report_id
- competitor_schema
- claims
- data_gaps
- potential_conflicts
- confidence_summary

### 4.6 qa_gate_results

- id
- report_id
- verdict
- scores
- issues
- recommendations
- rework_count

### 4.7 trace_steps

- id
- report_id
- stage
- expert
- task
- model
- prompt
- input
- output
- token_input
- token_output
- token_total
- duration_seconds
- status
- related_evidence_ids
- related_report_sections

### 4.8 annotations

- id
- report_id
- section_id
- selected_text
- annotation_type
- comment
- created_at
- source_position

### 4.9 research_memories

- id
- kind
- content
- confidence
- source
- evidence
- status
- created_at
- updated_at
- usage_rule

## 5. API 草案

### 5.1 Research

- `POST /api/research/preview`
  - 根据用户输入生成调研范围确认页预填信息。

- `POST /api/research`
  - 创建调研任务。

- `GET /api/research/:id`
  - 获取调研任务详情。

- `POST /api/research/:id/run`
  - 启动调研 workflow。

### 5.2 Reports

- `GET /api/reports`
- `GET /api/reports/:id`
- `PATCH /api/reports/:id/sections/:sectionId`
- `GET /api/reports/:id/graph`

### 5.3 Evidence

- `GET /api/reports/:id/evidence`
- `GET /api/evidence`
- `GET /api/evidence/:id`

### 5.4 Trace

- `GET /api/reports/:id/trace`
- `GET /api/trace/:stepId`

### 5.5 Experts

- `GET /api/experts`
- `GET /api/experts/:id`

### 5.6 Knowledge / Memory

- `GET /api/knowledge`
- `POST /api/knowledge`
- `GET /api/memories`
- `POST /api/memories/candidates`

## 6. 关键技术策略

### 6.1 先 Mock，再接真实 Workflow

开发顺序：

```text
mock 页面和数据
  -> 结构化存储
  -> Adapter 接 Evolva trace / skills / memory
  -> 真实证据采集
  -> 真实 Analysis Pack / QA Gate
```

原因：

- Verda 类产品页面复杂，先复刻形态更容易对齐产品体验。
- Agent Workflow 需要逐步接入，避免一开始陷入底层工程细节。

### 6.2 数据源边界

不以绕过反爬为能力。

优先支持：

- 公开网页。
- 搜索结果。
- 用户提供 URL。
- 用户上传资料。
- 示例数据。
- 合规第三方数据服务。

无法获取的数据必须标注缺口。

### 6.3 图表生成约束

任何图表必须绑定结构化数据表。

图表数据应标注：

- 指标名称。
- 指标值。
- 来源。
- 是否推断。
- 来源 URL。
- 备注。

推断数据不得伪装成事实数据。

### 6.4 记忆治理约束

默认不自动把所有报告内容写入 active memory。

可进入记忆候选：

- 用户明确要求记住。
- 用户标注为认同或亮点。
- 通过质检的高置信结论。
- 多次重复出现的研究模式。
- 返工中沉淀出的专家 lesson。

低置信、冲突、缺少证据、过期信息进入 draft 或 quarantined。

## 7. 待确认问题

- SQLite schema 是否在第一轮开发中落地。
- Evolva 真实接入方式优先采用 Python API、CLI wrapper，还是二者兼容。
- 是否在 P0 做真实网页抓取，还是先支持 URL + mock evidence。
