export const mockNavigationNotice = {
  dataSource: "mock",
  isRealWorkflow: false,
  note: "当前 Phase 1 只复刻产品形态，未接入真实 Evolva workflow。"
};

export const mockReports = [
  {
    id: "mock-001",
    title: "AI 协作写作竞品分析",
    competitors: ["Notion AI", "飞书妙记", "Gamma"],
    evidenceCount: 9,
    claimCount: 6,
    highConfidenceCount: 3,
    qaStatus: "pass",
    updatedAt: "2026-07-10",
    summary: "比较 AI 协作写作场景下的定位、定价和用户声音。"
  },
  {
    id: "mock-002",
    title: "B2B SaaS 定价策略研究",
    competitors: ["Linear", "Jira", "Asana"],
    evidenceCount: 6,
    claimCount: 4,
    highConfidenceCount: 2,
    qaStatus: "risk",
    updatedAt: "2026-07-09",
    summary: "识别免费层、团队版边界和企业版销售线索。"
  },
  {
    id: "mock-003",
    title: "生成式演示工具定位研究",
    competitors: ["Gamma", "Tome", "Canva AI"],
    evidenceCount: 4,
    claimCount: 3,
    highConfidenceCount: 1,
    qaStatus: "draft",
    updatedAt: "2026-07-08",
    summary: "比较从零生成、模板编辑和团队协作的差异。"
  }
];

export const mockScope = {
  goal: "分析 Notion AI、飞书妙记、Gamma 在 AI 协作写作场景下的产品策略、定价与用户反馈差异",
  domain: "AI 协作写作与知识工作台",
  competitors: ["Notion AI", "飞书妙记", "Gamma"],
  dimensions: ["产品定位", "核心场景", "定价策略", "用户声音", "证据缺口"],
  perspective: "AI 产品经理：机会识别与差异化策略",
  market: "中文与英文知识工作者",
  audience: "中小团队 PM / 运营 / 创作者",
  timeRange: "最近 12 个月公开资料"
};

export const mockPipeline = [
  { label: "范围确认", status: "done", detail: "竞品、市场、用户、时间范围已确认" },
  { label: "Orchestrator 计划", status: "done", detail: "拆解为 4 个只读研究任务" },
  { label: "证据采集", status: "active", detail: "Evidence Collector 正在整理来源" },
  { label: "交叉验证", status: "pending", detail: "等待 Evidence Pack" },
  { label: "QA Gate", status: "warn", detail: "准备检查 Analysis Pack" },
  { label: "报告生成", status: "pending", detail: "仅基于通过质检的结论" }
];

export const mockAgentActions = [
  {
    agent: "Research Orchestrator",
    badge: "计划已生成",
    body: "将 AI 协作写作竞品拆为产品定位、定价、用户声音、证据采集四组任务。工具边界限定为公开网页、用户 URL、上传文件和明确标识的示例数据。"
  },
  {
    agent: "Evidence Collector",
    badge: "新增 3 条 Mock 证据",
    body: "Notion AI 的官网套餐页可复查，但用户评价样本不足。当前不能支撑“市场整体口碑领先”的强结论。"
  },
  {
    agent: "Business / Pricing Analyst",
    badge: "待验证",
    body: "价格数字本身差异有限，真正影响决策的是套餐边界：AI 用量、导出能力、团队协作人数和管理员控制。"
  }
];

export const mockEvidence = [
  {
    id: "ev_mock_001",
    title: "Notion AI Pricing Page",
    source: "官网 · 可复查 · Mock timestamp",
    confidence: 86,
    level: "high",
    summary: "官网价格页，来源权威、可复查。真实接入后需要重新校验时效性与套餐内容。",
    url: "https://www.notion.so/product/ai"
  },
  {
    id: "ev_mock_002",
    title: "Gamma Product Page",
    source: "公开网页 · Mock source",
    confidence: 84,
    level: "high",
    summary: "支撑“展示型内容生成”定位判断。真实接入后点击会打开原始链接或用户上传材料。",
    url: "https://gamma.app"
  },
  {
    id: "ev_mock_003",
    title: "User Voice Sample",
    source: "示例数据 · 样本不足",
    confidence: 63,
    level: "medium",
    summary: "只允许作为风险提示，不支撑强结论。可加入知识库，但不自动写入 active memory。",
    url: "#mock-user-voice"
  }
];

export const mockTraceSteps = [
  {
    id: "trace_mock_001",
    stage: "Plan",
    expert: "Research Orchestrator",
    status: "done",
    duration: "5.2s",
    summary: "将用户目标拆解为证据采集、产品分析、定价分析和用户声音分析。"
  },
  {
    id: "trace_mock_002",
    stage: "QA Gate",
    expert: "QA Agent",
    status: "rework",
    duration: "3.7s",
    summary: "用户声音章节有 2 个强结论只绑定单一低可信样本，需要降级或补充证据。"
  }
];

export const mockExperts = [
  {
    id: "orchestrator",
    name: "Research Orchestrator",
    layer: "decision",
    role: "理解任务、拆解计划、选择专家、管理状态并汇总结果。",
    tools: ["workflow", "trace", "expert_router"],
    outputSchema: "research_plan"
  },
  {
    id: "evidence-collector",
    name: "Evidence Collector",
    layer: "execution",
    role: "采集公开网页、用户 URL 和上传材料，输出结构化 Evidence。",
    tools: ["web_fetch", "file_to_text"],
    outputSchema: "evidence_items"
  },
  {
    id: "qa-agent",
    name: "QA Agent",
    layer: "strategy",
    role: "检查 Analysis Pack 的证据充分性、结论可信度和数据缺口。",
    tools: ["qa_gate", "trace"],
    outputSchema: "qa_gate_result"
  }
];
