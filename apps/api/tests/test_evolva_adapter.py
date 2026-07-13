from verity_api.evolva_adapter import EvolvaAdapter
from verity_api.main import app

from fastapi.testclient import TestClient


client = TestClient(app)


def test_evolva_status_endpoint_exposes_adapter_capabilities() -> None:
    response = client.get("/api/evolva/status")

    assert response.status_code == 200
    item = response.json()["item"]
    assert item["available"] is True
    assert item["mode"] == "evolva-adapter"
    assert "traces_dir" in item
    assert "memory" in item
    assert "skills" in item
    assert "tools" in item


def test_smoke_trace_is_imported_as_verity_steps() -> None:
    response = client.post("/api/evolva/smoke-trace?report_id=mock-001")

    assert response.status_code == 200
    item = response.json()["item"]
    assert item["run_id"].startswith("run_")
    assert item["imported_trace_steps"] >= 1
    assert item["steps"][0]["source"]["runtime"] == "evolva"


def test_trace_mapping_redacts_sensitive_payload() -> None:
    adapter = EvolvaAdapter()
    recorder = adapter.create_smoke_trace()
    run_id = recorder["run_id"]
    trace = adapter.load_trace(run_id)
    trace["events"].append(
        {
            "ts": trace["started_at"],
            "kind": "tool_call",
            "event_id": "evt_secret",
            "data": {
                "tool": "web_fetch",
                "args": {
                    "api_key": "sk-abcdefghijklmnopqrstuvwxyz123456",
                    "url": "https://example.com",
                },
                "output": "Bearer abcdefghijklmnopqrstuvwxyz123456",
            },
        }
    )

    # Write a temporary augmented trace through the existing trace path so the
    # adapter exercises its normal load/map/redact path.
    path = adapter.config.traces_dir / f"{run_id}_secret.json"
    import json

    path.write_text(json.dumps(trace, ensure_ascii=False), encoding="utf-8")
    steps = adapter.trace_to_verity_steps(f"{run_id}_secret")
    rendered = json.dumps(steps, ensure_ascii=False)

    assert "sk-abcdefghijklmnopqrstuvwxyz123456" not in rendered
    assert "Bearer abcdefghijklmnopqrstuvwxyz123456" not in rendered
    assert "[REDACTED" in rendered


def test_bounded_local_evidence_workflow_persists_verity_chain() -> None:
    response = client.post("/api/evolva/workflows/bounded-local-evidence")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data_source"]["is_real_workflow"] is True
    assert payload["data_source"]["is_real_research"] is False
    item = payload["item"]
    assert item["ok"] is True
    assert item["workflow"]["workflow_id"] == "verity_bounded_local_evidence"
    assert item["evidence_count"] == 3
    assert item["claim_count"] == 3
    assert item["analysis_pack"]["claim_evidence_map"]
    assert item["qa_gate"]["verdict"] in {"pass", "rework"}
    assert item["trace_steps"] >= 2
