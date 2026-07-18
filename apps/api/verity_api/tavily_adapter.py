from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import os
from typing import Any, Iterable
from urllib.parse import urlparse

import httpx

from .scoring import score_evidence


TAVILY_BASE_URL = "https://api.tavily.com"


class TavilyProviderError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


@dataclass(frozen=True)
class TavilyStatus:
    available: bool
    reason: str
    provider: str = "tavily"

    def to_dict(self) -> dict[str, Any]:
        return {
            "available": self.available,
            "reason": self.reason,
            "provider": self.provider,
        }


class TavilyProvider:
    """Small HTTP adapter for Tavily Search and Extract."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = TAVILY_BASE_URL,
        timeout_seconds: float = 60.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=timeout_seconds,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def search(
        self,
        query: str,
        *,
        max_results: int = 5,
        search_depth: str = "basic",
        topic: str = "general",
        include_domains: list[str] | None = None,
        exclude_domains: list[str] | None = None,
    ) -> dict[str, Any]:
        if not query.strip():
            raise TavilyProviderError("query_required", "Tavily search query is required.")
        if not 0 <= max_results <= 20:
            raise TavilyProviderError("max_results_invalid", "Tavily max_results must be between 0 and 20.")
        payload = {
            "query": query.strip(),
            "search_depth": search_depth,
            "max_results": max_results,
            "topic": topic,
            "include_answer": False,
            "include_raw_content": False,
            "include_images": False,
            "include_domains": include_domains or [],
            "exclude_domains": exclude_domains or [],
            "include_usage": True,
        }
        return self._post("/search", payload)

    def extract(
        self,
        urls: Iterable[str],
        *,
        query: str = "",
        extract_depth: str = "basic",
    ) -> dict[str, Any]:
        normalized_urls = _normalize_urls(urls)
        if not normalized_urls:
            raise TavilyProviderError("urls_required", "At least one public http(s) URL is required.")
        if len(normalized_urls) > 20:
            raise TavilyProviderError("url_limit_exceeded", "Tavily Extract accepts at most 20 URLs per request.")
        payload: dict[str, Any] = {
            "urls": normalized_urls,
            "extract_depth": extract_depth,
            "format": "markdown",
            "include_images": False,
            "include_favicon": False,
            "include_usage": True,
        }
        if query.strip():
            payload["query"] = query.strip()
            payload["chunks_per_source"] = 3
        return self._post("/extract", payload)

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self._client.post(path, json=payload)
        except httpx.TimeoutException as exc:
            raise TavilyProviderError("provider_timeout", "Tavily request timed out.", retryable=True) from exc
        except httpx.HTTPError as exc:
            raise TavilyProviderError("provider_network_error", "Tavily request failed.", retryable=True) from exc

        if response.status_code == 401:
            raise TavilyProviderError("api_key_invalid", "Tavily rejected the API key.")
        if response.status_code == 429:
            raise TavilyProviderError("rate_limited", "Tavily rate limit was reached.", retryable=True)
        if response.status_code >= 500:
            raise TavilyProviderError("provider_server_error", "Tavily returned a server error.", retryable=True)
        if response.status_code >= 400:
            raise TavilyProviderError("provider_request_error", "Tavily rejected the request.")
        try:
            body = response.json()
        except ValueError as exc:
            raise TavilyProviderError("provider_response_invalid", "Tavily returned invalid JSON.") from exc
        if not isinstance(body, dict):
            raise TavilyProviderError("provider_response_invalid", "Tavily response must be an object.")
        return body


def get_tavily_status() -> dict[str, Any]:
    if _tavily_api_key():
        return TavilyStatus(available=True, reason="ready").to_dict()
    return TavilyStatus(available=False, reason="api_key_not_configured").to_dict()


def collect_public_web_evidence(
    *,
    query: str,
    user_urls: list[str] | None = None,
    max_results: int = 5,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    provider: TavilyProvider | None = None,
) -> dict[str, Any]:
    """Search and extract public web content into Verity evidence objects.

    Search snippets are retained only in collection_trace. Only successful Extract
    results become evidence_items, so a search result without readable page content
    cannot support a claim.
    """

    if not query.strip():
        return _collection_blocked("query_required")
    if not _tavily_api_key() and provider is None:
        return _collection_blocked("api_key_not_configured")

    owned_provider = provider is None
    provider = provider or TavilyProvider(api_key=_tavily_api_key())
    captured_at = datetime.now(timezone.utc).isoformat()
    trace: list[dict[str, Any]] = []
    attempts: list[dict[str, Any]] = []
    try:
        search_response = provider.search(
            query,
            max_results=max_results,
            include_domains=include_domains,
            exclude_domains=exclude_domains,
        )
        search_results = search_response.get("results", []) if isinstance(search_response, dict) else []
        search_urls = []
        for item in search_results:
            if not isinstance(item, dict) or not item.get("url"):
                continue
            url = str(item["url"])
            search_urls.append(url)
            trace.append(
                {
                    "stage": "search",
                    "url": url,
                    "title": item.get("title", ""),
                    "search_score": item.get("score"),
                    "used_as_evidence": False,
                    "note": "Search snippet is not evidence until page extraction succeeds.",
                }
            )

        requested_urls = _normalize_urls([*(user_urls or []), *search_urls])[:20]
        source_by_url = {
            url: ("user_provided_url" if url in _normalize_urls(user_urls or []) else "public_web")
            for url in requested_urls
        }
        try:
            extract_response = provider.extract(requested_urls, query=query)
        except TavilyProviderError as exc:
            attempts.append({"stage": "extract", "status": "failed", "code": exc.code, "retryable": exc.retryable})
            return _collection_result(query, [], attempts, trace, captured_at, search_response)

        extracted = extract_response.get("results", []) if isinstance(extract_response, dict) else []
        failed_results = extract_response.get("failed_results", []) if isinstance(extract_response, dict) else []
        for failed in failed_results:
            attempts.append({"stage": "extract", "status": "failed", **_safe_attempt(failed)})

        evidence_items = []
        for item in extracted:
            if not isinstance(item, dict):
                continue
            url = str(item.get("url", "")).strip()
            content = str(item.get("raw_content", "") or item.get("content", "")).strip()
            if not url or not content:
                attempts.append({"stage": "extract", "url": url, "status": "empty_content"})
                continue
            title = _title_for_url(url, search_results)
            source_type = source_by_url.get(url, "public_web")
            evidence = _to_evidence_item(
                url=url,
                title=title,
                content=content,
                source_type=source_type,
                captured_at=captured_at,
                search_results=search_results,
            )
            evidence_items.append(evidence)
            trace.append(
                {
                    "stage": "extract",
                    "url": url,
                    "status": "success",
                    "content_hash": evidence["content_hash"],
                    "used_as_evidence": True,
                }
            )
        return _collection_result(query, evidence_items, attempts, trace, captured_at, search_response)
    except TavilyProviderError as exc:
        return {
            "status": "failed",
            "reason": exc.code,
            "retryable": exc.retryable,
            "query": query,
            "evidence_items": [],
            "source_attempts": attempts,
            "collection_trace": trace,
            "captured_at": captured_at,
            "is_real_online_collection": False,
        }
    finally:
        if owned_provider:
            provider.close()


def collect_public_web_evidence_batch(
    *,
    queries: list[str],
    user_urls: list[str] | None = None,
    max_results: int = 5,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    provider: TavilyProvider | None = None,
) -> dict[str, Any]:
    """Collect several query slices into one deduplicated Run Evidence Store.

    Each query keeps its own search/extract trace. Search snippets remain trace
    only; only successful page extraction is promoted to evidence. User URLs are
    passed through on the first query and deduplicated with search results.
    """

    normalized_queries = [str(query).strip() for query in queries if str(query).strip()]
    if not normalized_queries:
        normalized_queries = ["用户提供的公开网页"] if user_urls else []
    if not normalized_queries:
        return {
            "status": "blocked",
            "reason": "query_required",
            "queries": [],
            "evidence_items": [],
            "query_results": [],
            "source_attempts": [],
            "collection_trace": [],
            "is_real_online_collection": False,
        }
    if not _tavily_api_key() and provider is None:
        return {
            "status": "blocked",
            "reason": "api_key_not_configured",
            "queries": normalized_queries,
            "evidence_items": [],
            "query_results": [],
            "source_attempts": [],
            "collection_trace": [],
            "is_real_online_collection": False,
        }

    owned_provider = provider is None
    provider = provider or TavilyProvider(api_key=_tavily_api_key())
    evidence_by_hash: dict[str, dict[str, Any]] = {}
    query_results: list[dict[str, Any]] = []
    attempts: list[dict[str, Any]] = []
    trace: list[dict[str, Any]] = []
    try:
        for index, query in enumerate(normalized_queries):
            result = collect_public_web_evidence(
                query=query,
                user_urls=user_urls if index == 0 else [],
                max_results=max_results,
                include_domains=include_domains,
                exclude_domains=exclude_domains,
                provider=provider,
            )
            query_results.append({
                "query": query,
                "status": result.get("status"),
                "reason": result.get("reason"),
                "evidence_count": len(result.get("evidence_items", [])),
                "search_request_id": result.get("search_request_id"),
                "search_usage": result.get("search_usage", {}),
            })
            for attempt in result.get("source_attempts", []):
                attempts.append({"query": query, **attempt})
            for entry in result.get("collection_trace", []):
                trace.append({"query": query, **entry})
            for item in result.get("evidence_items", []):
                dedupe_key = item.get("content_hash") or item.get("id")
                if dedupe_key and dedupe_key not in evidence_by_hash:
                    evidence_by_hash[dedupe_key] = item
        evidence_items = list(evidence_by_hash.values())
        return {
            "status": "completed" if evidence_items else "insufficient_evidence",
            "reason": "evidence_extracted" if evidence_items else "no_extractable_sources",
            "queries": normalized_queries,
            "evidence_items": evidence_items,
            "query_results": query_results,
            "source_attempts": attempts,
            "collection_trace": trace,
            "is_real_online_collection": bool(evidence_items),
        }
    finally:
        if owned_provider:
            provider.close()


def _to_evidence_item(
    *,
    url: str,
    title: str,
    content: str,
    source_type: str,
    captured_at: str,
    search_results: list[Any],
) -> dict[str, Any]:
    content_hash = hashlib.sha256(f"{url}\n{content}".encode("utf-8")).hexdigest()
    parsed = urlparse(url)
    search_score = next(
        (item.get("score") for item in search_results if isinstance(item, dict) and item.get("url") == url),
        None,
    )
    score_input = {
        "title": title,
        "url": url,
        "source_type": source_type,
        "platform": parsed.netloc,
        "publisher": parsed.netloc,
        "captured_at": captured_at,
        "retrieval_status": "success",
        "relevance": "direct" if search_score is not None else "partial",
        "specificity": "medium" if len(content) >= 300 else "low",
        "specific_signals": ["extracted_content"] if len(content) >= 300 else [],
        "risk_flags": [] if len(content) >= 300 else ["short_content"],
    }
    scored = score_evidence(score_input)
    return {
        "id": f"ev_tavily_{content_hash[:16]}",
        "title": title or parsed.netloc,
        "url": url,
        "source_type": source_type,
        "platform": parsed.netloc,
        "source_label": "Tavily Extract · public web" if source_type == "public_web" else "User-provided URL · Tavily Extract",
        "captured_at": captured_at,
        "retrieval_status": "success",
        "claim_types": [],
        "summary": content[:4000],
        "confidence": scored["confidence"],
        "confidence_level": scored["confidence_level"],
        "scores": scored["scores"],
        "risk_note": scored["risk_note"],
        "content_hash": content_hash,
        "search_relevance_score": search_score,
    }


def _collection_result(
    query: str,
    evidence_items: list[dict[str, Any]],
    attempts: list[dict[str, Any]],
    trace: list[dict[str, Any]],
    captured_at: str,
    search_response: dict[str, Any],
) -> dict[str, Any]:
    return {
        "status": "completed" if evidence_items else "insufficient_evidence",
        "reason": "evidence_extracted" if evidence_items else "no_extractable_sources",
        "query": query,
        "evidence_items": evidence_items,
        "source_attempts": attempts,
        "collection_trace": trace,
        "captured_at": captured_at,
        "search_request_id": search_response.get("request_id"),
        "search_usage": search_response.get("usage", {}),
        "is_real_online_collection": bool(evidence_items),
    }


def _collection_blocked(reason: str) -> dict[str, Any]:
    return {
        "status": "blocked",
        "reason": reason,
        "evidence_items": [],
        "source_attempts": [],
        "collection_trace": [],
        "is_real_online_collection": False,
    }


def _normalize_urls(urls: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    for raw_url in urls:
        url = str(raw_url).strip()
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            continue
        if url not in normalized:
            normalized.append(url)
    return normalized


def _title_for_url(url: str, search_results: list[Any]) -> str:
    for item in search_results:
        if isinstance(item, dict) and item.get("url") == url:
            return str(item.get("title", ""))
    return urlparse(url).netloc


def _safe_attempt(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return {key: value.get(key) for key in ("url", "error", "status") if key in value}
    return {"detail": str(value)}


def _tavily_api_key() -> str:
    return os.getenv("TAVILY_API_KEY", "").strip()
