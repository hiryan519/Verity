# Verity Design System

版本：v0.1  
状态：已定稿为当前阶段 UI 视觉规范  
视觉样例：`docs/verity-living-design-system.html`

本文档定义 Verity 后续 Web UI 开发的视觉、排版、组件和交互规范。后续实现页面时，应优先遵循本文档；如果与产品机制冲突，以 `AGENTS.md` 中的产品决策优先级为准。

## 1. 设计哲学

Verity 是面向专业产品经理的证据驱动竞品分析工作台，不是普通 SaaS 后台，也不是营销型 AI 工具。

核心气质：

- 专业、冷静、克制。
- 像干净明亮的温室玻璃房：结构清晰、透明、有秩序。
- 使用低饱和鼠尾草绿表达“研究、可信、沉静”。
- UI 退居幕后，让证据、结论、Trace 和质量门控成为主角。
- 不使用沉重阴影、花哨渐变、粗笨大圆角或装饰性图表。

关键词：

- Editorial SaaS。
- Greenhouse。
- Evidence-first。
- Quiet interface。
- Traceable intelligence。

## 2. 颜色系统

所有页面应使用低饱和、暖白、细线的基础系统。

| Token | Hex | 用途 |
| --- | --- | --- |
| `Bg-Workspace` | `#FAFAF8` | 全局桌面背景，带极轻微暖色，降低阅读疲劳 |
| `Bg-Surface` | `#FFFFFF` | 卡片、报告正文、面板主体 |
| `Border-Line` | `#E5E5E5` | 分割线、卡片边框、面板边界 |
| `Brand-Sage` | `#78907A` | 主按钮、强调标签、关键状态点 |
| `Brand-Sage-Light` | `#EAF0EA` | 次级背景、浅色标签、导航选中态 |
| `Text-Main` | `#333333` | 主标题与正文，不使用纯黑 |
| `Semantic-Warning` | `#F5A623` | 中置信、返工、待确认、QA 风险提示 |

使用规则：

- 大面积背景只使用 `Bg-Workspace` 或 `Bg-Surface`。
- 绿色只用于导航选中、主按钮、可信度标签、状态节点和轻强调。
- 橙色只用于风险、返工、中置信，不用于装饰。
- 图表颜色必须低饱和，并且必须绑定数据源或证据数量。
- 不使用紫蓝渐变、霓虹色、深色发光背景或营销式高对比色块。

## 3. 字体与排版

Verity 采用 Editorial SaaS 的混合排版策略：阅读和判断使用 serif，操作和数据使用 sans。

### 3.1 字体引入

当前视觉规范使用：

- `Inter`：UI 控件、导航、标签、数字、数据层。
- `Noto Serif SC`：展示标题、章节标题、报告正文、结论预览、长阅读内容。
- fallback：`system-ui`、`Georgia`、`serif`。

Web 实现可使用：

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Noto+Serif+SC:wght@400;500;600;700&display=swap" rel="stylesheet">
```

### 3.2 字体职责

使用 `font-serif` 的区域：

- 顶部大标题。
- 页面模块 H2。
- 报告正文。
- 结论预览文本。
- 需要形成“智库、出版、研究档案”气质的长文本。

使用 `font-sans` 的区域：

- 左侧导航。
- 顶部工具栏。
- 按钮。
- 输入控件。
- Pipeline 状态节点。
- Agent 状态卡片的元信息。
- 置信度标签。
- Citation Pill。
- 数据数字、时间戳、Token、耗时。
- Caption 和辅助说明。

重要规则：

- Serif 段落中嵌入的证据锚点、置信度标签仍然必须显式使用 sans。
- 长正文行高建议 `1.7` 或 `leading-relaxed`。
- UI 数据标签保持 `12px` 或 `text-xs`，不要放大成标题。
- 主正文建议 `14px`，报告正文可以在阅读页根据密度提升到 `15px` 或 `16px`，但需要保持三栏可读。

## 4. 材质与形状

核心原则：精密、扁平、轻量。

容器：

- 背景：`#FFFFFF`。
- 边框：`1px solid #E5E5E5`。
- 圆角：`12px`，Tailwind 可用 `rounded-xl`。
- 默认不使用阴影。

浮层：

- 仅悬浮工具条、下拉层、证据展开层可使用极弱阴影。
- 推荐 `shadow-sm` 或等价的极轻阴影。
- 禁止大面积弥散阴影、玻璃拟态重模糊和发光边框。

按钮与标签：

- 圆角：`6px`，Tailwind 可用 `rounded-md`。
- 高度保持紧凑。
- 主按钮使用 `Brand-Sage`。
- 次级按钮使用 `Brand-Sage-Light`。

## 5. 布局规范

Verity 的页面布局应服务于“调研、阅读、追溯”三类任务。

### 5.1 全局布局

- 全局背景使用 `Bg-Workspace`。
- 内容容器使用细边框区分结构，不靠阴影制造层级。
- 页面宽度应留出呼吸感，避免满屏铺满卡片。
- 重要页面优先使用清晰的左右或三栏结构。

### 5.2 首页 / 工作台

首页只负责发起调研，不承担复杂配置。

应包含：

- 自然语言输入。
- 示例任务。
- 少量专家协作氛围提示。

不应包含：

- 复杂模式切换。
- 过多图表。
- 未开始调研前的大量空状态解释。

### 5.3 调研执行页

推荐三栏：

- 左栏：任务流水线 / Pipeline。
- 中栏：Agent 动作流。
- 右栏：实时证据库。

交互重点：

- Agent 工作过程必须拆解为可理解动作。
- 右侧证据出现时需标注来源、时间、可信度、风险。
- Mock 数据必须明确标记为 Mock，不暗示真实抓取。

### 5.4 报告阅读页

推荐三栏：

- 左栏：报告目录。
- 中栏：报告正文。
- 右栏：证据 / 标注 / 知识库。

阅读规则：

- 报告正文使用 serif。
- 结论后紧跟 Citation Pill。
- 点击证据锚点应定位右侧证据卡，不应打断阅读流。
- 低置信、冲突、数据缺口必须在正文或侧栏显式提示。

### 5.5 决策链路页

决策链路不是原始日志倾倒，而是面向用户的决策回放。

应包含：

- 阶段筛选。
- 总 Token、耗时、步骤数。
- 单步 Prompt / Input / Output 展开。
- Agent、阶段、任务、状态、关联证据和关联报告章节。

展示前必须脱敏 API Key、Cookie、敏感输入等内容。

## 6. 关键组件

### 6.1 Confidence Tag

用途：展示证据或 Claim 的可信度。

推荐样式：

- 小胶囊形状。
- `rounded-md`。
- `text-xs`。
- 高置信：浅绿背景 + `Brand-Sage` 文本。
- 中置信：浅橙背景 + 橙色文本。
- 低置信：浅红背景 + 红色文本。

文案建议：

- `高置信 86`
- `中置信 64`
- `低置信 38`

规则：

- 可信度必须来自多维度评分，不允许简单按来源类型粗暴打分。
- 低置信不能支撑强结论。
- 标签属于数据层，必须使用 sans。

### 6.2 Citation Pill

用途：跟随在结论性文字后，连接报告正文和证据侧栏。

推荐样式：

- `rounded-md`。
- 细边框或浅绿背景。
- `text-xs`。
- 文案如 `🔗 2条证据`。

规则：

- Citation Pill 不应过大，不能破坏正文阅读节奏。
- 点击后优先在右侧证据栏展开或高亮证据。
- 如果证据不足，应显示 `证据不足` 或 `数据缺口`，而不是隐藏。

### 6.3 Agent Action Card

用途：展示 Agent 当前动作、工具边界和阶段输出。

应包含：

- Agent 头像或角色标识。
- Agent 名称。
- 当前动作。
- 状态标签。
- 简短输出摘要。
- 相关证据或风险提示。

规则：

- Agent Action Card 是过程透明度组件，不是聊天气泡。
- 不应伪装为真人对话。
- 如果是 Mock 状态，必须显式标注。

### 6.4 Evidence Card

用途：展示证据库中的单条证据。

应包含：

- 标题。
- URL 或文件来源。
- 来源类型。
- 平台。
- 抓取或导入时间。
- 摘要。
- 可信度总分。
- 风险提示。

规则：

- 证据卡的视觉重点是可复查性和风险，不是装饰。
- 低置信或无法打开的证据必须标注。
- 多源支持可以作为补充说明，但不能替代证据明细。

### 6.5 Annotation Toolbar

用途：报告阅读页中对段落或选中文本进行标注。

建议操作：

- 亮点。
- 存疑。
- 加入知识库。
- 批注。

规则：

- 该工具条是浮层，可使用极弱 shadow。
- 加入知识库不等于写入 Research Memory。
- 用户主动收藏、标注或确认的内容才可进入 memory candidate。

## 7. 状态与语义

状态色必须服务于判断，不用于装饰。

| 状态 | 视觉 | 使用场景 |
| --- | --- | --- |
| 完成 | `Brand-Sage` | 阶段完成、证据通过、QA pass |
| 进行中 | `Brand-Sage` 或浅绿脉冲 | Agent 正在执行 |
| 等待 | `Border-Line` / 灰文本 | 尚未开始的 Pipeline 节点 |
| 中置信 / 返工 | `Semantic-Warning` | QA rework、证据不足、待确认 |
| 失败 / 高风险 | 红色系 | 抓取失败、证据冲突、不可复查 |

QA Gate 不通过时：

- Trace 中必须突出失败节点。
- 展示返工原因。
- 展示 rework_count。
- 最多返工 1 次。

## 8. 数据与图表

图表必须有数据依据。

允许：

- 明确标注 Mock 的示例图。
- 由 Evidence Pack 或结构化数据表支撑的图表。
- 图表旁展示 `数据依据：X条证据` 或 `查看数据源`。

禁止：

- 无数据表支撑的装饰性图表。
- 用图表暗示不存在的全网舆情。
- 用低置信样本生成强趋势结论。

## 9. Mock 与真实能力标识

当前阶段允许使用 Mock 做形态验证，但必须明确标识。

Mock 必须做到：

- 文件名、接口名或页面标签能看出是 Mock。
- 页面文案不暗示真实在线抓取。
- 证据、Trace、QA、Memory 不得被静态假数据冒充为真实接入。

真实接入后必须做到：

- 标注数据来源。
- 展示采集时间。
- 保留工具调用边界。
- 输出可复查证据。
- Trace 展示前脱敏。

## 10. Tailwind 落地建议

推荐在后续前端实现中配置以下 token：

```js
colors: {
  workspace: "#FAFAF8",
  surface: "#FFFFFF",
  line: "#E5E5E5",
  sage: "#78907A",
  "sage-light": "#EAF0EA",
  ink: "#333333",
  warning: "#F5A623"
}
```

```js
fontFamily: {
  sans: ["Inter", "system-ui", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "PingFang SC", "Microsoft YaHei", "sans-serif"],
  serif: ['"Noto Serif SC"', "Georgia", "serif"]
}
```

常用 class 建议：

- 页面背景：`bg-workspace text-ink font-sans`
- 主内容面板：`rounded-xl border border-line bg-surface`
- 浅绿面板：`rounded-xl border border-line bg-sage-light`
- 标签：`rounded-md px-2.5 py-1 text-xs font-medium`
- 阅读正文：`font-serif text-sm leading-relaxed`
- UI 元信息：`font-sans text-xs text-ink/50`
- 弱浮层：`shadow-sm`

## 11. 可访问性与可读性

- 正文必须保持足够对比度，主文本使用 `Text-Main` 或其透明度变体。
- 长正文控制行宽，避免超过舒适阅读长度。
- 交互元素需要明确 hover / active / focus 状态。
- 标签不能只依赖颜色表达状态，需配合文字。
- 响应式布局中不能隐藏关键证据、Trace 或 QA 风险。

## 12. 开发验收清单

每次 UI 开发完成后至少检查：

- 是否使用本文档指定颜色 token。
- 标题和阅读层是否使用 serif。
- UI 控件、标签和数据层是否使用 sans。
- 卡片是否保持 1px 细边框和轻量圆角。
- 是否避免重阴影、渐变、装饰性图表。
- 证据锚点是否能定位或关联证据。
- Mock 是否明确标识。
- 低置信、冲突、数据缺口是否可见。
- Trace 展示是否脱敏。
- 页面是否能在常见桌面宽度下稳定阅读。

## 13. 当前视觉基准

当前定稿视觉基准为：

- `docs/verity-living-design-system.html`

后续如果设计发生变化，应优先更新该 HTML，再同步更新本文档。
