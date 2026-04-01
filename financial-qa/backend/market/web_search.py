"""General web search via Tavily — fallback for knowledge questions not in the RAG corpus.

Tavily is an AI-optimized search API designed for LLM/RAG applications. It returns
clean, pre-extracted content suitable for passing directly to Claude, unlike raw
HTML snippets from generic search APIs.

Requires TAVILY_API_KEY in the environment (.env file).
"""

import os
from dataclasses import dataclass


@dataclass
class WebResult:
    title: str
    url: str
    snippet: str


def web_search(query: str, max_results: int = 5) -> list[WebResult]:
    """Return up to *max_results* web results for *query* via Tavily.

    Uses search_depth="advanced" for deeper content extraction — better quality
    for financial concept and current-events questions.
    Returns empty list on any error (API key missing, network failure, etc.).
    """
    items: list[WebResult] = []
    try:
        from tavily import TavilyClient
        api_key = os.environ.get("TAVILY_API_KEY", "")
        if not api_key:
            return items
        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
        )
        for r in response.get("results", []):
            items.append(WebResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                snippet=r.get("content", ""),
            ))
    except Exception:
        pass

    return items
