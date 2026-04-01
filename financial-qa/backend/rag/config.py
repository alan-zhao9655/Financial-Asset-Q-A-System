"""Central configuration for the RAG pipeline.

All tunable parameters live here. To swap the embedding model:
  1. Change EMBEDDING_MODEL and EMBEDDING_DIM below
  2. Re-run `python -m rag.indexer` — the indexer detects the mismatch and rebuilds.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_RAG_DIR = Path(__file__).parent
DOCUMENTS_DIR = _RAG_DIR / "data" / "documents"
INDEX_PATH    = _RAG_DIR / "data" / "knowledge.faiss"
META_PATH     = _RAG_DIR / "data" / "knowledge_meta.json"

# ---------------------------------------------------------------------------
# Embedding model
# bge-m3: 1024-dim, 570MB, 100+ languages. Purpose-built for Chinese/English
# cross-lingual retrieval (created by BAAI). No manual query/document prefixes
# needed — bge-m3 uses a unified encoder for both, unlike bge-small/e5.
# Runs on Apple Silicon via MPS (Metal Performance Shaders) for fast inference.
# Upgrade path: change EMBEDDING_MODEL + EMBEDDING_DIM, then re-run indexer.
# ---------------------------------------------------------------------------
EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DIM   = 1024   # must match the model above

# ---------------------------------------------------------------------------
# Reranker model (cross-encoder, sentence-transformers, ~1.1GB)
# bge-reranker-v2-m3 is the companion to bge-m3 — both built by BAAI for
# Chinese/English cross-lingual retrieval. Handles (Chinese query, English
# passage) pairs correctly, which ms-marco-MiniLM (English-only) cannot.
# ---------------------------------------------------------------------------
RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"

# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------
CHUNK_TARGET_TOKENS  = 400   # target chunk size in whitespace-tokens (words)
CHUNK_OVERLAP_TOKENS = 50    # trailing overlap carried into the next chunk
CHUNK_MIN_TOKENS     = 60    # paragraphs smaller than this are merged into the next

# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------
RETRIEVE_TOP_K = 20   # number of candidates FAISS retrieves (broad recall)
RERANK_TOP_K   = 5    # number of results returned after cross-encoder reranking

# ---------------------------------------------------------------------------
# Web search fallback
# ---------------------------------------------------------------------------
# bge-reranker-v2-m3 outputs sigmoid scores (0–1).
# If the top reranked chunk scores below this threshold, the corpus likely
# doesn't have a good answer — fall back to DuckDuckGo web search.
# Calibration: highly relevant ≥0.7, moderate 0.35–0.7, irrelevant <0.35.
RERANK_CONFIDENCE_THRESHOLD = 0.35
