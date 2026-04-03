"""
RAG retrieval quality evaluation — no API calls required.

Metrics computed:
  - Hit@1   : is the top-1 retrieved parent from an expected source?
  - Hit@5   : is any of the top-5 retrieved parents from an expected source?
  - MRR     : Mean Reciprocal Rank — 1/rank of first expected source in top-5
  - Reranker lift: % of queries where reranking moved the expected source higher
                   than its FAISS-only ranking
  - Avg top-1 rerank score for hits vs misses (confidence calibration check)

Methodology:
  - Loads labeled queries from data/retrieval_labels.json
  - Each entry specifies which document filename(s) should appear in top-5
  - Runs the full two-stage retrieval pipeline (FAISS + bge-reranker-v2-m3)
  - Also runs FAISS-only retrieval to measure reranker lift
  - The "source" field in parent chunks is the .md filename (e.g. "pe_ratio.md")

Usage:
    cd financial-qa/backend
    ../../.venv/bin/python ../evaluation/test_retrieval.py

No API key required — purely local models.
"""

from __future__ import annotations

import json
import sys
import numpy as np
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

DATA_FILE = Path(__file__).parent / "data" / "retrieval_labels.json"


def _normalise_source(source: str) -> str:
    """Strip .md extension for comparison."""
    return source.replace(".md", "").lower().strip()


def faiss_only_retrieve(question: str, top_k: int = 5) -> list[dict]:
    """Retrieve using FAISS only (no reranking) for lift measurement."""
    from rag.retriever import _ensure_loaded, _index, _children, _parents
    import numpy as np
    from rag.config import RETRIEVE_TOP_K
    from rag.embedder import get_embedder

    _ensure_loaded()
    embedder = get_embedder()
    query_vec = embedder.embed_query(question).reshape(1, -1).astype(np.float32)

    distances, indices = _index.search(query_vec, RETRIEVE_TOP_K)

    seen_parents: set[str] = set()
    result: list[dict] = []

    for dist, idx in zip(distances[0], indices[0]):
        if idx < 0:
            continue
        child = _children[idx]
        pid   = child["parent_id"]
        if pid in seen_parents:
            continue
        seen_parents.add(pid)

        parent = dict(_parents[pid])
        parent["faiss_score"] = float(dist)
        result.append(parent)

        if len(result) >= top_k:
            break

    return result


def rank_of_first_hit(retrieved: list[dict], expected_sources: list[str]) -> int | None:
    """Return the 1-based rank of the first expected source in the retrieved list, or None."""
    norm_expected = {_normalise_source(s) for s in expected_sources}
    for rank, chunk in enumerate(retrieved, start=1):
        if _normalise_source(chunk.get("source", "")) in norm_expected:
            return rank
    return None


def run_evaluation():
    from rag.retriever import retrieve

    cases = json.loads(DATA_FILE.read_text())
    print(f"Running retrieval evaluation on {len(cases)} labeled queries...\n")
    print("(Loading models — this may take ~30s on first run)")
    print()

    hits_at_1    = 0
    hits_at_5    = 0
    reciprocal_ranks: list[float] = []
    reranker_lifts   = 0
    reranker_total   = 0

    scores_hits:   list[float] = []
    scores_misses: list[float] = []

    failures: list[dict] = []

    for i, case in enumerate(cases):
        query    = case["query"]
        expected = case["expected_sources"]

        print(f"  [{i+1:02d}/{len(cases)}] {case['id']}: {query[:55]}", end=" ... ", flush=True)

        # Full two-stage retrieval
        retrieved = retrieve(query, top_k=5)

        # FAISS-only retrieval for lift measurement
        faiss_retrieved = faiss_only_retrieve(query, top_k=5)

        # Compute metrics
        rank = rank_of_first_hit(retrieved, expected)
        faiss_rank = rank_of_first_hit(faiss_retrieved, expected)

        hit1 = rank == 1
        hit5 = rank is not None
        rr   = 1.0 / rank if rank else 0.0

        if hit1:
            hits_at_1 += 1
        if hit5:
            hits_at_5 += 1
        reciprocal_ranks.append(rr)

        # Reranker lift: did reranking move the expected source to a better rank?
        if faiss_rank is not None and rank is not None:
            reranker_total += 1
            if rank < faiss_rank:
                reranker_lifts += 1

        # Score calibration
        top_score = retrieved[0]["rerank_score"] if retrieved else 0.0
        if hit5:
            scores_hits.append(top_score)
        else:
            scores_misses.append(top_score)

        # Print result
        if hit1:
            print(f"Hit@1  score={top_score:.3f}")
        elif hit5:
            print(f"Hit@5  rank={rank}  score={top_score:.3f}")
        else:
            print(f"MISS   score={top_score:.3f}")
            failures.append({
                "id": case["id"],
                "query": query,
                "expected": expected,
                "retrieved_sources": [_normalise_source(c.get("source", "")) for c in retrieved],
            })

    total = len(cases)
    mrr   = sum(reciprocal_ranks) / total if total else 0.0

    print(f"\n{'='*60}")
    print(f"RETRIEVAL METRICS  (n={total})")
    print(f"{'='*60}")
    print(f"  Hit@1          : {hits_at_1}/{total} = {hits_at_1/total*100:.1f}%")
    print(f"  Hit@5          : {hits_at_5}/{total} = {hits_at_5/total*100:.1f}%")
    print(f"  MRR            : {mrr:.3f}")

    if reranker_total > 0:
        print(f"\n  Reranker lift  : {reranker_lifts}/{reranker_total} queries improved ({reranker_lifts/reranker_total*100:.1f}%)")

    if scores_hits:
        print(f"\n  Avg top-1 rerank score:")
        print(f"    Hits  : {sum(scores_hits)/len(scores_hits):.3f}  (n={len(scores_hits)})")
    if scores_misses:
        print(f"    Misses: {sum(scores_misses)/len(scores_misses):.3f}  (n={len(scores_misses)})")

    if failures:
        print(f"\nMissed cases ({len(failures)}):")
        for f in failures:
            print(f"  [{f['id']}] expected={f['expected']}")
            print(f"        retrieved={f['retrieved_sources']}")
            print(f"        query: {f['query'][:60]}")
    else:
        print("\nAll cases retrieved at least one expected source!")


if __name__ == "__main__":
    run_evaluation()
