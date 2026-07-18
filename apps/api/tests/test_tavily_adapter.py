import httpx

from verity_api import db
from verity_api.tavily_adapter import (
    TavilyProvider,
    TavilyProviderError,
    collect_public_web_evidence,
    collect_public_web_evidence_batch,
    get_tavily_status,
)


def test_tavily_status_is_blocked_without_key(monkeypatch) -> None:
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    status = get_tavily_status()

    assert status["available"] is False
    assert status["reason"] == "api_key_not_configured"


def test_tavily_provider_sends_search_and_extract_requests_without_live_network() -> None:
    paths = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        if request.url.path == "/search":
            return httpx.Response(200, json={"results": [{"title": "Example", "url": "https://example.com", "score": 0.91}]}, request=request)
        return httpx.Response(200, json={"results": [{"url": "https://example.com", "raw_content": "Extracted page content."}], "failed_results": []}, request=request)

    provider = TavilyProvider(
        api_key="tvly-test",
        transport=httpx.MockTransport(handler),
    )
    search = provider.search("example pricing", max_results=1)
    extract = provider.extract(["https://example.com"], query="example pricing")
    provider.close()

    assert paths == ["/search", "/extract"]
    assert search["results"][0]["score"] == 0.91
    assert extract["results"][0]["raw_content"] == "Extracted page content."


def test_tavily_provider_maps_unauthorized_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"detail": "unauthorized"}, request=request)

    provider = TavilyProvider(api_key="tvly-invalid", transport=httpx.MockTransport(handler))
    try:
        provider.search("example")
    except TavilyProviderError as exc:
        assert exc.code == "api_key_invalid"
    else:
        raise AssertionError("expected Tavily API key error")
    finally:
        provider.close()


def test_collection_only_promotes_successful_extracts_to_evidence() -> None:
    class FakeProvider:
        def search(self, query: str, **kwargs):
            return {
                "request_id": "search-1",
                "usage": {"credits": 1},
                "results": [
                    {"title": "Example page", "url": "https://example.com/page", "score": 0.82, "content": "snippet"},
                    {"title": "Unreadable page", "url": "https://example.com/unreadable", "score": 0.76, "content": "snippet"},
                ],
            }

        def extract(self, urls, **kwargs):
            return {
                "results": [{"url": "https://example.com/page", "raw_content": "A sufficiently long extracted page body."}],
                "failed_results": [{"url": "https://example.com/unreadable", "error": "blocked"}],
            }

    result = collect_public_web_evidence(
        query="example pricing",
        user_urls=["https://user.example/source"],
        provider=FakeProvider(),
    )

    assert result["status"] == "completed"
    assert len(result["evidence_items"]) == 1
    evidence = result["evidence_items"][0]
    assert evidence["url"] == "https://example.com/page"
    assert evidence["content_hash"]
    assert evidence["search_relevance_score"] == 0.82
    assert evidence["confidence"] != evidence["search_relevance_score"]
    assert result["source_attempts"][0]["status"] == "failed"
    assert all(item["used_as_evidence"] is False for item in result["collection_trace"] if item["stage"] == "search")


def test_collection_requires_key_when_no_test_provider(monkeypatch) -> None:
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    result = collect_public_web_evidence(query="example pricing")

    assert result["status"] == "blocked"
    assert result["reason"] == "api_key_not_configured"


def test_collected_evidence_persists_content_hash(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "verity.db")
    db.init_db()
    result = collect_public_web_evidence(
        query="example pricing",
        provider=type(
            "Provider",
            (),
            {
                "search": lambda self, query, **kwargs: {
                    "results": [{"title": "Example", "url": "https://example.com", "score": 0.9}]
                },
                "extract": lambda self, urls, **kwargs: {
                    "results": [{"url": "https://example.com", "raw_content": "Extracted content."}],
                    "failed_results": [],
                },
            },
        )(),
    )

    assert db.persist_collected_evidence("mock-001", result["evidence_items"]) == 1
    stored = db.list_evidence("mock-001")
    stored_item = next(item for item in stored if item["id"] == result["evidence_items"][0]["id"])

    assert stored_item["content_hash"] == result["evidence_items"][0]["content_hash"]


def test_batch_collection_deduplicates_content_hash_across_queries() -> None:
    class FakeProvider:
        def search(self, query: str, **kwargs):
            suffix = "same" if "product" in query else "other"
            return {"results": [{"title": suffix, "url": f"https://example.com/{suffix}", "score": 0.8}]}

        def extract(self, urls, **kwargs):
            url = urls[0]
            content = "The same extracted page body." if url.endswith("/same") else "A second extracted page body."
            return {"results": [{"url": url, "raw_content": content}], "failed_results": []}

    result = collect_public_web_evidence_batch(
        queries=["product", "product follow-up", "pricing"],
        provider=FakeProvider(),
    )

    assert result["status"] == "completed"
    assert len(result["query_results"]) == 3
    assert len(result["evidence_items"]) == 2
    assert len({item["content_hash"] for item in result["evidence_items"]}) == 2
    assert all("query" in entry for entry in result["collection_trace"])
