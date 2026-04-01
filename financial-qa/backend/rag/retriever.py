"""RAG retrieval orchestrator — parent-child pipeline.

Two-stage retrieval:
  1. Embed query → FAISS search over child chunks (precise bi-encoder match)
  2. Cross-encoder rerank the top-RETRIEVE_TOP_K child candidates
  3. Map reranked children back to their parent sections (deduped)
  4. Return parent sections as context for the LLM

The LLM receives full section text (~400 tokens) even though retrieval was done on
small child chunks (~100 tokens). This avoids the precision vs. context trade-off:
  - Small chunks → sharp embeddings → better FAISS matching
  - Full parents → complete context → better LLM answers

Both models are lazy singletons. The FAISS index is cached at module level.
"""

from __future__ import annotations

import numpy as np

from rag.config import RETRIEVE_TOP_K, RERANK_TOP_K
from rag.embedder import get_embedder
from rag.reranker import get_reranker
from rag.indexer import load_index

# ---------------------------------------------------------------------------
# Module-level cache
# ---------------------------------------------------------------------------
_index = None
_children: list[dict] | None = None
_parents: dict[str, dict] | None = None


def _ensure_loaded():
    global _index, _children, _parents
    if _index is None:
        _index, _children, _parents = load_index()


def retrieve(question: str, top_k: int = RERANK_TOP_K) -> list[dict]:
    """Retrieve the most relevant parent sections for a question.

    Pipeline:
      embed query → FAISS top-RETRIEVE_TOP_K children → rerank children →
      map to parents (deduplicated) → return top_k parents

    Args:
        question: The user's natural-language question.
        top_k:    Number of parent sections to return.

    Returns:
        List of parent chunk dicts sorted by relevance (best first), each with:
        text, source, title, section, parent_id, rerank_score.
        The "text" field is the full parent section (~400 tokens), suitable for
        passing directly to the LLM as context.

    Raises:
        RuntimeError: if the index has not been built yet.
    """
    _ensure_loaded()

    embedder = get_embedder()
    query_vec = embedder.embed_query(question).reshape(1, -1).astype(np.float32)

    # Step 1: broad FAISS recall over child chunks
    distances, indices = _index.search(query_vec, RETRIEVE_TOP_K)

    child_candidates = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < 0:
            continue
        child = dict(_children[idx])
        child["faiss_score"] = float(dist)
        child_candidates.append(child)

    # Step 2: rerank children for precision
    reranker = get_reranker()
    reranked_children = reranker.rerank(question, child_candidates, top_k=RETRIEVE_TOP_K)

    # Step 3: map children → parents, deduplicate, preserve order
    seen_parents: set[str] = set()
    result: list[dict] = []

    for child in reranked_children:
        pid = child["parent_id"]
        if pid in seen_parents:
            continue
        seen_parents.add(pid)

        parent = dict(_parents[pid])
        parent["rerank_score"] = child["rerank_score"]
        result.append(parent)

        if len(result) >= top_k:
            break

    return result
