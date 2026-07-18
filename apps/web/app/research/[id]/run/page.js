import { ResearchRunClient } from "@/components/research-run-client";

export default async function ResearchRunPage({ params }) {
  const { id } = await params;
  return <ResearchRunClient runId={id} />;
}
