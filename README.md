# Verity

面向产品经理的、证据前置的多 Agent 竞品研究系统。

Verity 将竞品分析从“一次性生成报告”重构为一条可编排、可验证、可追踪的研究 Workflow：多领域专家 Agent 在明确边界内协作，核心结论必须经过证据治理、交叉验证和 QA 质检，最终报告保留可复查的研究过程，并将有效反馈沉淀为受治理的 Research Memory。

## 核心 Workflow

```text
研究目标输入
  → 调研范围确认（Human Gate）
  → 研究编排与专家选择
  → 证据采集 / 产品分析 / 定价分析 / 用户体验分析
  → 共享证据库
  → 交叉验证
  → QA Gate
  → 报告撰写与交付
  → Decision Trace
  → Research Memory / Skill 沉淀
```

Verity 保留真正的多 Agent 架构。专家是具备独立职责、工具权限、输入输出契约和 Trace 的任务执行单元；Skill 是专家可调用或后续沉淀的方法、规则与 checklist，不是专家本体。

## 核心机制

### 1. 证据前置的结论准入

Verity 使用“证据 → 可验证结论 → 结构化分析包 → QA 质量门控 → 最终报告”的分层链路。证据不只是报告生成后的引用说明，而是约束结论生成与报告准入的核心机制。

每条 Evidence 尽量保留来源 URL、采集时间、内容摘要、`content_hash`、多维度质量评分和风险提示；核心 Claim 必须绑定可复查证据，弱证据、冲突和数据缺口需要显式降级或披露。

### 2. 多 Agent 专家协作

当前专家体系包括：

- 研究编排专家
- 证据采集专家
- 产品分析专家
- 定价策略专家
- 用户体验分析专家
- 交叉验证专家
- QA 质检专家
- 报告撰写专家

互不依赖的只读研究任务可以并行；交叉验证、QA 和报告撰写按依赖顺序收敛。运行时可根据竞品、维度、Evidence Slice、Claim 数量和 Token 预算拆分同类型专家实例，避免把全部上下文一次性塞给单个 Agent。

### 3. 双层质量门控

报告生成前设置交叉验证和 QA 质检：

- 交叉验证汇总不同专家 Pack 中的冲突、错配、过强结论和 `data_gap`。
- QA Gate 基于 QA Brief 检查证据充分性、维度覆盖、结论可信度、结构完整性、证据一致性和数据缺口风险。
- P0 最多返工 1 次；仍未达标时必须降级交付、披露风险或请求人工确认，避免 Agent 无限循环。

### 4. 决策链路白盒化

Expert Registry 展示专家长期治理信息，Decision Trace 展示单次运行中的阶段性研究产物和执行事实。Trace 会对 Prompt、输入输出、模型、Token、耗时、状态及关联证据等信息进行脱敏映射，用于过程复盘和问题定位，而不是直接倾倒原始日志。

### 5. 基于反馈的受控演进

证据库、知识库和历史报告都不等于 Research Memory。用户批注、QA 返工和交叉验证结果可以形成 Memory Candidate；候选经验只有在明确作用对象、试用结果和风险边界后，才可能升级为 Active Memory，并影响后续专家 checklist 或执行上下文。

当前治理状态包括 `candidate`、`active`、`quarantined` 和 `archived`。每个专家的 Memory 召回数量受预算限制，负反馈可以触发隔离或回滚，避免错误经验持续污染后续任务。

## 技术架构

```text
Next.js Web Console
  → FastAPI Adapter / Business Layer
  → Verity Workflow、Evidence、QA、Trace、Memory
  → Evolva Agent Infra
  → SQLite / Local Runtime Files
```

- **前端**：Next.js 16、React 19、Tailwind CSS 4
- **后端**：FastAPI
- **本地存储**：SQLite
- **Agent Infra**：Evolva Workflow、Trace、Memory、Skill 与 Tool Runtime
- **接入原则**：通过轻量 Adapter / wrapper 复用 Evolva，不为页面展示深改底层核心逻辑

## 项目结构

```text
apps/
  web/                  Next.js Web Console
  api/                  FastAPI Adapter、SQLite 与业务机制
docs/
  TODO.md               开发任务与验收记录
  MECHANISM.md          核心产品机制
  ARCHITECTURE.md       工程架构与接入边界
  DECISION_LOG.md       关键产品决策
  DESIGN.md             UI 视觉规范
evolva/                 上游 Evolva Agent Infra
```

## 本地运行

环境要求：Python 3.10+、Node.js 与 npm。

### 1. 启动 FastAPI

在仓库根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m pip install -r apps\api\requirements.txt -r apps\api\requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn verity_api.main:app --app-dir apps\api --reload --host 127.0.0.1 --port 8000
```

API 健康检查：<http://127.0.0.1:8000/health>

API 文档：<http://127.0.0.1:8000/docs>

### 2. 启动 Web Console

打开另一个终端：

```powershell
cd apps\web
npm ci
npm run dev
```

访问：<http://127.0.0.1:3000>

前端默认请求 `http://127.0.0.1:8000`。如需修改，可在启动前设置 `VERITY_API_BASE_URL`。

## 验证

```powershell
# API tests（在仓库根目录进入 apps/api）
cd apps\api
..\..\.venv\Scripts\python.exe -m pytest tests -q

# Web production build（另开终端，在仓库根目录执行）
cd apps\web
npm run build
```

## 研究数据边界

Verity 的研究数据范围聚焦于公开网页与用户主动提供的 URL。系统区分公开来源、用户资料、结构化本地数据和 Agent 运行数据，并为证据保留来源、采集时间、内容摘要、内容哈希、质量评分与风险提示。

无法访问、来源不明、样本不足或存在冲突的信息会被显式标记；搜索结果只用于发现候选来源，不能直接替代可复查证据。系统不以登录、绕过访问限制或规避反爬作为研究能力。

## 进一步阅读

- [核心产品机制](docs/MECHANISM.md)
- [工程架构](docs/ARCHITECTURE.md)
- [关键决策日志](docs/DECISION_LOG.md)
- [设计规范](docs/DESIGN.md)

## 上游基础与许可

Verity 在 [Evolva](https://github.com/koppx/Evolva) Agent Infra 之上增加 Web 产品层、竞品研究业务层和可视化治理能力。Evolva 的原始代码与相关资产继续遵循仓库中的上游许可；Verity 新增部分沿用本仓库许可约束。
