from fastapi.testclient import TestClient

from verity_api.main import app
from verity_api.verity_experts import READ_ONLY_PARALLEL_EXPERTS, VerityExpertRunner


client = TestClient(app)


def test_verity_expert_library_uses_product_experts_not_default_coder_role() -> None:
    runner = VerityExpertRunner()
    experts = runner.list_experts()
    expert_ids = {expert["id"] for expert in experts}

    assert "research_orchestrator" in expert_ids
    assert "evidence_collector" in expert_ids
    assert "cross_validator" in expert_ids
    assert "qa_agent" in expert_ids
    assert "coder" not in expert_ids


def test_minimal_expert_run_has_parallel_read_only_experts_and_analysis_pack() -> None:
    response = client.post("/api/verity/experts/run-minimal?report_id=mock-001")

    assert response.status_code == 200
    item = response.json()["item"]
    assert item["is_real_workflow"] is False
    assert len(item["expert_results"]) >= 3
    assert len(item["parallel_experts"]) >= 2
    assert set(READ_ONLY_PARALLEL_EXPERTS).issubset(set(item["parallel_experts"]))
    assert item["analysis_pack"]["claim_evidence_map"]
    assert item["qa_gate"]["verdict"] in {"pass", "rework"}


def test_verity_expert_endpoint_lists_cross_validation_agent() -> None:
    response = client.get("/api/verity/experts")

    assert response.status_code == 200
    items = response.json()["items"]
    names = {item["name"] for item in items}
    assert "Cross-validation Agent" in names
