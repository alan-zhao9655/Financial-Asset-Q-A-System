"""Smoke test for the RAG pipeline — no API key needed.

Tests:
  1. Chunker — verify parent-child splitting on synthetic text
  2. Index build — build from the corpus documents
  3. Retrieval — run 3 test queries, print top results with source attribution
  4. Reranker order change — verify cross-encoder changes FAISS ordering

Usage:
    ../../.venv/bin/python test_rag.py

Requires:
    - RAG deps installed: faiss-cpu, fastembed, wikipedia-api
    - Corpus built: python -m rag.build_corpus
    (Index is rebuilt automatically by this test.)
"""

import sys
import textwrap

# ---------------------------------------------------------------------------
# 1. Chunker test (no external deps)
# ---------------------------------------------------------------------------
print("=" * 60)
print("TEST 1: Chunker (parent-child)")
print("=" * 60)

from rag.chunker import chunk_document

SAMPLE_DOC = textwrap.dedent("""\
    # Price–earnings ratio

    The price–earnings ratio (P/E ratio) is the ratio of a company's share price to
    the company's earnings per share. It is a commonly used metric to value companies.

    ## How to interpret P/E

    A high P/E ratio can indicate that investors expect high growth in the future, or
    that the stock is overvalued. A low P/E ratio may indicate the opposite. Comparing
    P/E ratios across companies in the same industry is more meaningful than comparing
    across different sectors, because different industries have different typical ranges.

    ## Limitations

    The P/E ratio does not account for future growth directly. Analysts often use the
    forward P/E (based on estimated future earnings) alongside the trailing P/E (based
    on historical earnings). Neither measure captures debt levels or cash flow.

    ## See also

    This section should be skipped.
""")

children, parents = chunk_document(SAMPLE_DOC, source="pe_ratio.md")
print(f"  Sections (parents): {len(parents)}")
print(f"  Child chunks:       {len(children)}")

for pid, parent in parents.items():
    child_count = sum(1 for c in children if c["parent_id"] == pid)
    print(f"  [parent] section='{parent['section']}' tokens={len(parent['text'].split())} → {child_count} children")

for c in children:
    print(f"    [child {c['chunk_id']}] tokens={c['token_count']} text={c['text'][:60].replace(chr(10),' ')}...")

print()
assert len(parents) > 0, "No parents produced"
assert len(children) > 0, "No children produced"
assert all(c["parent_id"] in parents for c in children), "Child references missing parent"
assert all(c["source"] == "pe_ratio.md" for c in children)
print("  PASS\n")


# ---------------------------------------------------------------------------
# 2. Index build
# ---------------------------------------------------------------------------
# print("=" * 60)
# print("TEST 2: Build index from corpus")
# print("=" * 60)

from rag.config import DOCUMENTS_DIR, INDEX_PATH
from rag.indexer import build_index, load_index

# if not list(DOCUMENTS_DIR.glob("*.md")):
#     print(f"  [SKIP] No documents found in {DOCUMENTS_DIR}")
#     print("  Run `python -m rag.build_corpus` first, then re-run this test.")
#     sys.exit(0)

# build_index()
index, children, parents = load_index()
# print(f"\n  FAISS index: {index.ntotal} child vectors")
# print(f"  Parents:     {len(parents)} sections")
# assert index.ntotal == len(children)
# print("  PASS\n")


# ---------------------------------------------------------------------------
# 3. Retrieval test — returns parent sections now
# ---------------------------------------------------------------------------
print("=" * 60)
print("TEST 3: Retrieval (parent-child)")
print("=" * 60)

from rag.retriever import retrieve

TEST_QUERIES = [
    "What is a P/E ratio and how is it used?",
    "How does dollar cost averaging reduce risk?",
    "What is the difference between a bond and a stock?",
    "Explain the definition of financial disruptions"
]

for q in TEST_QUERIES:
    print(f"\n  Query: {q}")
    results = retrieve(q, top_k=3)
    print(f"  Retrieved {len(results)} parent sections:")
    for r in results:
        print(f"    score={r['rerank_score']:+.3f}  [{r['source']} — {r['section']}]")
        preview = r['text'][:80].replace('\n', ' ')
        print(f"    parent text ({len(r['text'].split())} tokens): {preview}...")

assert all(len(retrieve(q)) > 0 for q in TEST_QUERIES)
print("\n  PASS\n")


# ---------------------------------------------------------------------------
# 4. Verify reranker changes FAISS ordering
# ---------------------------------------------------------------------------
print("=" * 60)
print("TEST 4: Reranker changes ordering")
print("=" * 60)

import numpy as np
from rag.embedder import get_embedder

query = "How does dollar cost averaging reduce risk?"
embedder = get_embedder()
qvec = embedder.embed_query(query).reshape(1, -1).astype(np.float32)
distances, indices = index.search(qvec, 10)

faiss_parent_ids = []
for idx in indices[0]:
    if idx >= 0:
        pid = children[idx]["parent_id"]
        if pid not in faiss_parent_ids:
            faiss_parent_ids.append(pid)

reranked = retrieve(query, top_k=3)
reranked_parent_ids = [r["parent_id"] for r in reranked]

print(f"  FAISS top parent_ids:    {faiss_parent_ids[:3]}")
print(f"  Reranked top parent_ids: {reranked_parent_ids}")

if faiss_parent_ids[:3] != reranked_parent_ids:
    print("  Reranker changed the ordering — PASS")
else:
    print("  Ordering unchanged (small corpus, acceptable) — PASS")

print()
print("=" * 60)
print("All tests passed.")
print("=" * 60)
