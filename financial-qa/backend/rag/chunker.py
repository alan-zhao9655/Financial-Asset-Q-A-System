"""Section-aware parent-child chunker for the RAG pipeline.

Architecture: parent-child (small-to-big) chunking
  1. Parse the markdown document into sections by detecting ## headers.
  2. Each section becomes a PARENT chunk (~400 tokens of context for the LLM).
  3. Each parent is split into CHILD chunks (~100 tokens each, with overlap).
  4. Only children are embedded and stored in FAISS.
  5. At retrieval time, children are retrieved first (precise match), then their
     parent text is returned to the LLM (complete context).

Why this is better than flat chunking:
  - Children are small → focused embeddings → better cosine similarity match
  - LLM receives the full parent section → complete context, no cut-off sentences
  - If a relevant passage spans a child boundary, the parent covers it whole

Chunk metadata:
  Child chunks (stored in FAISS):
    {
      "text":        str,   # the child text (~100 tokens)
      "parent_id":   str,   # key into the parents dict: "{source}::{section_idx}"
      "source":      str,   # filename, e.g. "pe_ratio.md"
      "title":       str,   # document title
      "section":     str,   # section header text
      "chunk_id":    int,   # 0-based global index across all children
      "token_count": int,
    }

  Parent chunks (stored in metadata sidecar, NOT in FAISS):
    {
      "parent_id": str,
      "text":      str,   # full section text (~400 tokens)
      "source":    str,
      "title":     str,
      "section":   str,
    }

Token counting uses whitespace splitting — fast and sufficient for chunking decisions.
"""

from __future__ import annotations

import re
from typing import NamedTuple

from rag.config import CHUNK_TARGET_TOKENS, CHUNK_OVERLAP_TOKENS, CHUNK_MIN_TOKENS

# Child chunk target — small for precise embedding, large enough to be meaningful
CHILD_TARGET_TOKENS  = 100
CHILD_OVERLAP_TOKENS = 20


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _token_count(text: str) -> int:
    return len(text.split())


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences on '.', '!', '?' followed by whitespace or EOL."""
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [p for p in parts if p]


def _tail_tokens(text: str, n: int) -> str:
    """Return the last n whitespace-tokens of text as a string."""
    tokens = text.split()
    return " ".join(tokens[-n:]) if len(tokens) > n else text


class _Section(NamedTuple):
    title: str    # header text; empty string for intro before first ##
    text: str     # raw content


def _parse_sections(markdown: str) -> tuple[str, list[_Section]]:
    """Split markdown into (doc_title, list[_Section]).

    The first # H1 becomes the document title.
    Every ## or deeper header starts a new section.
    Text before the first ## is the document intro (title = "").
    """
    lines = markdown.splitlines()
    doc_title = ""
    sections: list[_Section] = []
    current_title = ""
    current_lines: list[str] = []

    for line in lines:
        h1 = re.match(r'^#\s+(.+)', line)
        hx = re.match(r'^#{2,}\s+(.+)', line)

        if h1 and not doc_title:
            doc_title = h1.group(1).strip()
            continue

        if hx:
            body = "\n".join(current_lines).strip()
            if body:
                sections.append(_Section(title=current_title, text=body))
            current_title = hx.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)

    body = "\n".join(current_lines).strip()
    if body:
        sections.append(_Section(title=current_title, text=body))

    return doc_title, sections


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def chunk_document(text: str, source: str) -> tuple[list[dict], dict[str, dict]]:
    """Chunk a document into parent sections and child sub-chunks.

    Args:
        text:   Full markdown content.
        source: Filename (e.g. "pe_ratio.md") — stored in metadata.

    Returns:
        (children, parents) where:
          children — list of child chunk dicts (to be embedded in FAISS)
          parents  — dict mapping parent_id → parent chunk dict (stored in metadata)
    """
    doc_title, sections = _parse_sections(text)
    children: list[dict] = []
    parents: dict[str, dict] = {}
    child_id = 0

    for section_idx, section in enumerate(sections):
        parent_id = f"{source}::{section_idx}"

        # Build parent text: trim to CHUNK_TARGET_TOKENS but keep it as a whole section
        parent_text = _build_parent_text(section.text)

        parents[parent_id] = {
            "parent_id": parent_id,
            "text":      parent_text,
            "source":    source,
            "title":     doc_title,
            "section":   section.title,
        }

        # Split parent into child chunks
        section_children = _make_children(
            parent_text,
            parent_id=parent_id,
            source=source,
            title=doc_title,
            section=section.title,
            start_id=child_id,
        )
        children.extend(section_children)
        child_id += len(section_children)

    return children, parents


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_parent_text(text: str) -> str:
    """Build a parent chunk from a section's raw text.

    Limits the parent to CHUNK_TARGET_TOKENS to avoid oversized context.
    If the section is longer, it's truncated at sentence boundaries.
    """
    text = text.strip()
    if _token_count(text) <= CHUNK_TARGET_TOKENS:
        return text

    # Truncate at sentence boundary within token budget
    sentences = _split_sentences(text)
    kept: list[str] = []
    total = 0
    for s in sentences:
        st = _token_count(s)
        if total + st > CHUNK_TARGET_TOKENS and kept:
            break
        kept.append(s)
        total += st
    return " ".join(kept)


def _make_children(
    parent_text: str,
    parent_id: str,
    source: str,
    title: str,
    section: str,
    start_id: int,
) -> list[dict]:
    """Split a parent text into small child chunks with overlap."""
    sentences = _split_sentences(parent_text)
    if not sentences:
        return []

    children: list[dict] = []
    chunk_id = start_id
    overlap_carry = ""
    acc: list[str] = []
    acc_tokens = 0

    if overlap_carry:
        acc.append(overlap_carry)
        acc_tokens = _token_count(overlap_carry)

    for sent in sentences:
        sent_tokens = _token_count(sent)

        if acc_tokens + sent_tokens > CHILD_TARGET_TOKENS and acc:
            child_text = " ".join(acc)
            if _token_count(child_text) >= CHUNK_MIN_TOKENS:
                children.append({
                    "text":        child_text,
                    "parent_id":   parent_id,
                    "source":      source,
                    "title":       title,
                    "section":     section,
                    "chunk_id":    chunk_id,
                    "token_count": _token_count(child_text),
                })
                chunk_id += 1
            overlap_carry = _tail_tokens(child_text, CHILD_OVERLAP_TOKENS)
            acc = [overlap_carry] if overlap_carry else []
            acc_tokens = _token_count(overlap_carry)

        acc.append(sent)
        acc_tokens += sent_tokens

    # Flush remaining
    if acc:
        child_text = " ".join(acc)
        if _token_count(child_text) >= CHUNK_MIN_TOKENS:
            children.append({
                "text":        child_text,
                "parent_id":   parent_id,
                "source":      source,
                "title":       title,
                "section":     section,
                "chunk_id":    chunk_id,
                "token_count": _token_count(child_text),
            })
        elif children:
            # Small tail — merge into the previous child to avoid a fragment
            prev = children[-1]
            merged = prev["text"] + " " + child_text
            children[-1] = {**prev, "text": merged, "token_count": _token_count(merged)}
        else:
            # Entire section is small — emit as a single child anyway.
            # Every parent must have at least one child or it becomes unretrievable.
            children.append({
                "text":        child_text,
                "parent_id":   parent_id,
                "source":      source,
                "title":       title,
                "section":     section,
                "chunk_id":    chunk_id,
                "token_count": _token_count(child_text),
            })

    return children
