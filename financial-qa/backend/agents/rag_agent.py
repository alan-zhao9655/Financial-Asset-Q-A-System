"""Knowledge (RAG) agent — answers financial concept questions from the corpus.

Flow:
  1. Retrieve top-5 parent sections via FAISS + cross-encoder reranking.
  2. Check the top rerank_score against RERANK_CONFIDENCE_THRESHOLD (0.35).
     - Score >= threshold → answer from RAG corpus (Wikipedia-sourced, curated).
     - Score < threshold  → fall back to Tavily Search web search, which covers
       current events, niche topics, and questions not in the 50-article corpus.
  3. Build a grounded prompt with source attribution.
  4. Call Claude Sonnet and return the structured answer.

All CPU-bound operations (FAISS, model inference, Tavily Search) are run in a
thread pool to avoid blocking the async event loop.

Follows the same lazy-client pattern as market_agent.py.
"""

from __future__ import annotations

import asyncio
import logging
from functools import lru_cache

from anthropic import AsyncAnthropic

log = logging.getLogger(__name__)

from rag.retriever import retrieve
from rag.config import RERANK_CONFIDENCE_THRESHOLD
from market.web_search import web_search
from prompts.rag_prompt import (
    KNOWLEDGE_SYSTEM_PROMPT,
    build_knowledge_prompt,
    WEB_SEARCH_SYSTEM_PROMPT,
    build_web_search_prompt,
)


@lru_cache(maxsize=1)
def _get_client() -> AsyncAnthropic:
    return AsyncAnthropic()


async def handle_knowledge_query(question: str) -> str:
    """Answer a financial concept question using RAG with web search fallback.

    Args:
        question: The user's question (already understood and refined by the
                  understanding agent).

    Returns:
        A structured answer string with cited sources.

    Raises:
        RuntimeError: if the RAG index has not been built (propagated from retriever).
    """
    # Retrieval is synchronous (FAISS + model inference) — run in thread pool
    chunks = await asyncio.to_thread(retrieve, question)

    client = _get_client()

    # --- RAG path: corpus has a confident answer ---
    top_score = chunks[0].get("rerank_score", 0) if chunks else 0.0
    if chunks and top_score >= RERANK_CONFIDENCE_THRESHOLD:
        sources = [c.get("source", "?") for c in chunks]
        log.info(
            "[RAG] source=rag | top_score=%.3f | docs=%d | sources=%s",
            top_score, len(chunks), sources,
        )
        prompt = build_knowledge_prompt(question, chunks)
        message = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=KNOWLEDGE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    # --- Web search fallback: corpus confidence too low ---
    log.info("[RAG] source=web_search | top_score=%.3f (below threshold %.2f)", top_score, RERANK_CONFIDENCE_THRESHOLD)
    results = await asyncio.to_thread(web_search, question + " finance")

    if not results:
        log.warning("[RAG] web_search returned no results")
        # Both RAG and web search came up empty
        return (
            "I wasn't able to find relevant information to answer your question. "
            "Try rephrasing, or ask about a specific financial concept like "
            "P/E ratio, dividends, bonds, or ETFs."
        )

    log.info("[RAG] web_search returned %d results | urls=%s", len(results), [r.url for r in results])
    prompt = build_web_search_prompt(question, results)
    message = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=WEB_SEARCH_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text
