"""Cross-encoder reranker for the RAG pipeline.

Uses sentence-transformers CrossEncoder with MPS acceleration on Apple Silicon.
Model: BAAI/bge-reranker-v2-m3 (~1.1GB)
  - Companion model to bge-m3 — both built by BAAI for Chinese/English retrieval
  - Handles (Chinese query, English passage) cross-lingual pairs correctly
  - ms-marco-MiniLM (English-only) cannot do this reliably
  - max_length=512 — our parent chunks are ~400 tokens, well within limit

Graceful fallback: if the model fails to load, returns FAISS-ordered results rather
than raising an exception. System degrades to single-stage retrieval, not failure.
"""

from __future__ import annotations

import logging

from rag.config import RERANKER_MODEL, RERANK_TOP_K

logger = logging.getLogger(__name__)


def _get_device() -> str:
    try:
        import torch
        if torch.backends.mps.is_available():
            return "mps"
        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    return "cpu"


class CrossEncoderReranker:
    """Wraps sentence-transformers CrossEncoder with MPS support."""

    def __init__(self, model_name: str = RERANKER_MODEL) -> None:
        self._model_name = model_name
        self._model = None
        self._available: bool | None = None

    def _load(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            from sentence_transformers.cross_encoder import CrossEncoder
            device = _get_device()
            # max_length=512: our parent chunks are ~400 tokens, safely within limit.
            # bge-reranker-v2-m3 supports up to 8192 tokens but 512 is sufficient here
            # and keeps inference fast on MPS.
            self._model = CrossEncoder(self._model_name, device=device, max_length=512)
            self._available = True
        except Exception as exc:
            logger.warning(
                "Cross-encoder reranker unavailable (%s: %s). "
                "Falling back to FAISS cosine similarity ordering.",
                type(exc).__name__, exc,
            )
            self._available = False
        return self._available

    def rerank(
        self,
        query: str,
        chunks: list[dict],
        top_k: int = RERANK_TOP_K,
    ) -> list[dict]:
        """Re-score chunks against the query and return the best top_k."""
        if not chunks:
            return []

        if self._load():
            pairs = [(query, chunk["text"]) for chunk in chunks]
            try:
                scores = self._model.predict(pairs)
                ranked = sorted(zip(scores, chunks), key=lambda x: x[0], reverse=True)
                result = []
                for score, chunk in ranked[:top_k]:
                    augmented = dict(chunk)
                    augmented["rerank_score"] = float(score)
                    result.append(augmented)
                return result
            except Exception as exc:
                logger.warning("Reranking failed (%s). Using FAISS ordering.", exc)

        # Fallback: return top_k in FAISS order
        result = []
        for chunk in chunks[:top_k]:
            augmented = dict(chunk)
            augmented["rerank_score"] = chunk.get("faiss_score", 0.0)
            result.append(augmented)
        return result


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_reranker: CrossEncoderReranker | None = None


def get_reranker() -> CrossEncoderReranker:
    """Return the process-wide reranker singleton."""
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoderReranker()
    return _reranker
