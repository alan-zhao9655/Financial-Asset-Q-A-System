"""FAISS index builder and manager for the RAG pipeline.

Parent-child architecture:
  - Child chunks (~100 tokens) are embedded and stored in the FAISS index.
  - Parent chunks (~400 tokens, the sections they came from) are stored only in
    the JSON metadata sidecar — they are NOT embedded or indexed in FAISS.
  - At query time: retrieve child chunks for precision, return parent text for context.

Usage:
    python -m rag.indexer          # build or rebuild the full index
    python -m rag.indexer --check  # print index stats and exit

Metadata sidecar (knowledge_meta.json):
  {
    "embedding_model": str,
    "embedding_dim":   int,
    "num_children":    int,
    "children":        list[dict],   # i-th element = i-th FAISS vector
    "parents":         dict[str, dict]  # parent_id → parent chunk
  }
"""

from __future__ import annotations

import json
import sys
import argparse
from pathlib import Path

from rag.config import (
    DOCUMENTS_DIR,
    INDEX_PATH,
    META_PATH,
    EMBEDDING_MODEL,
    EMBEDDING_DIM,
)
from rag.chunker import chunk_document
from rag.embedder import get_embedder


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build_index(documents_dir: Path = DOCUMENTS_DIR) -> None:
    """Chunk all documents, embed children, and write FAISS index + metadata to disk."""
    import faiss

    md_files = sorted(documents_dir.glob("*.md"))
    if not md_files:
        raise FileNotFoundError(
            f"No .md files found in {documents_dir}. "
            "Run `python -m rag.build_corpus` first."
        )

    print(f"Building index from {len(md_files)} documents in {documents_dir}\n")

    embedder = get_embedder()
    all_children: list[dict] = []
    all_parents: dict[str, dict] = {}

    for path in md_files:
        text = path.read_text(encoding="utf-8")
        children, parents = chunk_document(text, source=path.name)
        all_children.extend(children)
        all_parents.update(parents)
        print(f"  {path.name:<45} {len(parents):>3} sections → {len(children):>4} child chunks")

    print(f"\nTotal: {len(all_parents)} sections, {len(all_children)} child chunks")
    print("Embedding... ", end="", flush=True)

    texts = [c["text"] for c in all_children]
    vectors = embedder.embed_documents(texts)   # (N, D), float32, L2-normalised

    print("done")

    dim = vectors.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(vectors)

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_PATH))

    meta = {
        "embedding_model": EMBEDDING_MODEL,
        "embedding_dim":   dim,
        "num_children":    len(all_children),
        "children":        all_children,
        "parents":         all_parents,
    }
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Index saved    → {INDEX_PATH}")
    print(f"Metadata saved → {META_PATH}")
    print(f"\nDone: {len(all_children)} child vectors, {len(all_parents)} parents, dim={dim}")


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

def load_index():
    """Load the FAISS index and metadata from disk.

    Returns:
        (faiss.Index, list[dict], dict[str, dict]) — index, children list, parents dict.

    Raises:
        RuntimeError: if index files don't exist or model config doesn't match.
    """
    import faiss

    if not INDEX_PATH.exists() or not META_PATH.exists():
        raise RuntimeError(
            "RAG index not built. Run `python -m rag.indexer` first."
        )

    meta = json.loads(META_PATH.read_text(encoding="utf-8"))

    if meta.get("embedding_model") != EMBEDDING_MODEL:
        raise RuntimeError(
            f"Index was built with model '{meta['embedding_model']}' but config "
            f"specifies '{EMBEDDING_MODEL}'. Re-run `python -m rag.indexer`."
        )
    if meta.get("embedding_dim") != EMBEDDING_DIM:
        raise RuntimeError(
            f"Index dimension {meta['embedding_dim']} != config EMBEDDING_DIM "
            f"{EMBEDDING_DIM}. Re-run `python -m rag.indexer`."
        )

    index = faiss.read_index(str(INDEX_PATH))
    children = meta["children"]
    parents = meta["parents"]
    return index, children, parents


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the RAG FAISS index.")
    parser.add_argument("--check", action="store_true", help="Print index stats and exit")
    args = parser.parse_args()

    if args.check:
        try:
            index, children, parents = load_index()
            meta = json.loads(META_PATH.read_text(encoding="utf-8"))
            print(f"Index:    {INDEX_PATH}")
            print(f"Children: {len(children)} (vectors in FAISS)")
            print(f"Parents:  {len(parents)} (sections, context for LLM)")
            print(f"Model:    {meta['embedding_model']}")
            print(f"Dim:      {meta['embedding_dim']}")
        except RuntimeError as e:
            print(f"[ERROR] {e}")
            sys.exit(1)
    else:
        build_index()
