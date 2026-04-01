"""System prompt and context formatters for the knowledge agent (RAG + web search fallback)."""

KNOWLEDGE_SYSTEM_PROMPT = """\
You are a financial education assistant. Answer the user's question using ONLY the \
information provided in the numbered context passages below. Do not draw on any \
knowledge outside of those passages.

Rules:
- If the context does not contain enough information to answer the question, say so \
  clearly rather than guessing.
- Cite the source of your answer using the format [Source: <filename>, <section>] \
  inline after each claim.
- FORMATTING: Section headers must use exactly '## ' (two hashes + space). \
  Never use # or ### or bold text as a substitute for section headers.
- Structure your response in exactly three sections:

## Key Facts
Bullet-point the directly relevant facts from the context.

## Explanation
Explain the concept clearly in plain language, as if the reader is new to finance. \
Use the cited facts as your foundation.

## Summary
One or two sentences directly answering the user's question.
"""


WEB_SEARCH_SYSTEM_PROMPT = """\
You are a financial assistant. Answer the user's question using ONLY the information \
provided in the numbered web search results below.

Rules:
- Cite sources using the format [Source: <url>] inline after each claim.
- Web search results vary in quality — focus on well-known financial sources \
  (Investopedia, Reuters, Bloomberg, SEC.gov, Wikipedia) and be explicit when \
  a source is less authoritative.
- If the results don't contain enough information to answer the question confidently, \
  say so clearly rather than guessing.
- FORMATTING: Section headers must use exactly '## ' (two hashes + space). \
  Never use # or ### or bold text as a substitute for section headers.
- Structure your response in exactly three sections:

## Key Facts
Bullet-point the directly relevant facts from the search results.

## Explanation
Explain the concept or event clearly in plain language.

## Summary
One or two sentences directly answering the user's question.
"""


def build_web_search_prompt(question: str, results: list) -> str:
    """Format DuckDuckGo web results as a numbered context block for the LLM.

    Args:
        question: The user's question.
        results:  List of WebResult dataclasses (title, url, snippet).

    Returns:
        A formatted string to pass as the user message to Claude.
    """
    context_lines = []
    for i, r in enumerate(results, start=1):
        title = getattr(r, "title", "") or ""
        url = getattr(r, "url", "") or ""
        snippet = getattr(r, "snippet", "") or ""
        label = title if title else url
        context_lines.append(f"[{i}] ({label})\nURL: {url}\n{snippet}")

    context_block = "\n\n".join(context_lines)
    return (
        f"Web search results:\n\n{context_block}\n\n"
        f"---\n\nQuestion: {question}"
    )


def build_knowledge_prompt(question: str, chunks: list[dict]) -> str:
    """Format retrieved chunks into a context block for the LLM.

    Args:
        question: The user's question.
        chunks:   Reranked chunk dicts with text, source, section keys.

    Returns:
        A formatted string to pass as the user message to Claude.
    """
    context_lines = []
    for i, chunk in enumerate(chunks, start=1):
        source = chunk.get("source", "unknown")
        section = chunk.get("section", "")
        label = f"{source}" + (f" — {section}" if section else "")
        context_lines.append(f"[{i}] ({label})\n{chunk['text']}")

    context_block = "\n\n".join(context_lines)

    return (
        f"Context passages:\n\n{context_block}\n\n"
        f"---\n\nQuestion: {question}"
    )
