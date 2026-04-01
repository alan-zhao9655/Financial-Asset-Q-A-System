"""Embedding provider for the RAG pipeline.

Design:
  - EmbeddingProvider protocol — swap embedding backends via config.py without
    changing the retriever. Change EMBEDDING_MODEL + EMBEDDING_DIM, rebuild index.
  - SentenceTransformerEmbedder — wraps sentence-transformers on Apple MPS.
    Uses BAAI/bge-m3 (1024-dim, 570MB), purpose-built for Chinese/English retrieval.
  - MPS acceleration — on Apple Silicon, inference runs on the Metal GPU (MPS).
    Falls back to CPU automatically if MPS is unavailable.
  - Lazy singleton — model loads on first use, not at import time.
  - All embeddings are L2-normalised so inner product == cosine similarity,
    matching FAISS IndexFlatIP.

Why bge-m3 over multilingual-e5-large:
  bge-m3 is smaller (570MB vs 2.24GB), faster on MPS, and scores higher on Chinese
  retrieval benchmarks. It was built specifically for cross-lingual Chinese/English
  retrieval by BAAI (Beijing Academy of AI), making it the natural choice for this
  bilingual financial Q&A system.

Why no query prefix:
  Unlike bge-small and e5 models, bge-m3 uses a unified encoder — queries and
  documents are encoded the same way. No prefix manipulation needed.
"""

from __future__ import annotations

from typing import Protocol
import numpy as np

from rag.config import EMBEDDING_MODEL


def _get_device() -> str:
    """Return 'mps' on Apple Silicon, 'cuda' if available, else 'cpu'."""
    try:
        import torch
        if torch.backends.mps.is_available():
            return "mps"
        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    return "cpu"


class EmbeddingProvider(Protocol):
    """Protocol any embedding backend must satisfy."""

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        """Return shape (N, D) float32 array, L2-normalised."""
        ...

    def embed_query(self, text: str) -> np.ndarray:
        """Return shape (D,) float32 array, L2-normalised."""
        ...

    @property
    def dimension(self) -> int:
        """Embedding dimension D."""
        ...


class SentenceTransformerEmbedder:
    """Wraps a sentence-transformers model as an EmbeddingProvider.

    Lazy-loaded: model is downloaded and initialised on first embed call.
    Device is selected automatically: MPS > CUDA > CPU.
    """

    def __init__(self, model_name: str = EMBEDDING_MODEL) -> None:
        self._model_name = model_name
        self._model = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            device = _get_device()
            self._model = SentenceTransformer(self._model_name, device=device)
            print(f"  [embedder] loaded {self._model_name} on {device}")
        return self._model

    @property
    def dimension(self) -> int:
        return self._load().get_sentence_embedding_dimension()

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        """Encode document texts. bge-m3 uses the same encoder for queries and docs."""
        model = self._load()
        vectors = model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
            batch_size=32,
        )
        return vectors.astype(np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        """Encode a single query. bge-m3 needs no special prefix."""
        model = self._load()
        vector = model.encode(
            text,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return vector.astype(np.float32)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_embedder: SentenceTransformerEmbedder | None = None


def get_embedder() -> SentenceTransformerEmbedder:
    """Return the process-wide embedder singleton."""
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformerEmbedder()
    return _embedder
