const API_BASE_URL = process.env.VERITY_API_BASE_URL || "http://127.0.0.1:8000";

export async function getApiData(path) {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      cache: "no-store"
    });

    if (!response.ok) {
      return { dataSource: null, items: [], error: `API returned ${response.status}` };
    }

    const payload = await response.json();
    return {
      dataSource: payload.data_source,
      item: payload.item,
      items: payload.items || [],
      error: null
    };
  } catch (error) {
    return {
      dataSource: null,
      item: null,
      items: [],
      error: error instanceof Error ? error.message : "API unavailable"
    };
  }
}

export function toReportCard(report) {
  return {
    id: report.id,
    title: report.title,
    competitors: report.competitors,
    evidenceCount: report.evidence_count,
    claimCount: report.claim_count,
    highConfidenceCount: report.high_confidence_count,
    qaStatus: report.qa_status,
    updatedAt: report.updated_at,
    summary: report.summary
  };
}

export function toExpertCard(expert) {
  return {
    id: expert.id,
    name: expert.name,
    layer: expert.layer,
    role: expert.responsibility || expert.role,
    tools: expert.tool_permissions || expert.tool_scope || [],
    outputSchema: expert.output_pack_type || expert.output_schema,
    supportsMultiInstance: Boolean(expert.supports_multi_instance),
    instanceStrategy: expert.instance_strategy || ""
  };
}

export function toolStatusLabel(status) {
  return status === "allowed" ? "允许" : "禁用";
}
