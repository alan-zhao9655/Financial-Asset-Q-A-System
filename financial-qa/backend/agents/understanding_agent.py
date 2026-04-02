import os
import logging
import anthropic
from market.ticker_resolver import resolve_ticker
from agents.market_agent import handle_market_query
from agents.rag_agent import handle_knowledge_query
from agents.comparison_agent import handle_comparison_query

log = logging.getLogger(__name__)


def _parse_tickers(raw: str) -> list[str]:
    """Split a potentially comma/space-separated ticker string into clean symbols."""
    return [s.strip().upper() for s in raw.replace(",", " ").split() if s.strip()]

_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


_SYSTEM_PROMPT = """\
You are a financial assistant that helps users articulate what they need before routing \
their request to the right part of a financial Q&A system.

The system has two capabilities:
- MARKET: live/recent data for a specific stock or asset — price, % change, volume, \
  news, P/E, 52-week range, earnings, volatility, trend analysis
- KNOWLEDGE: explaining financial concepts, definitions, how instruments work — \
  questions whose answers don't depend on live data

YOUR ROLE:
Assess whether the user's request is specific enough to fulfill. If not, ask one clear \
clarifying question to move closer. Keep asking until both conditions are met:
  1. intent_clarity = high  (you know exactly what they want)
  2. asset_resolved = yes   (specific stock/asset identified) OR not_needed (pure concept)

ASSESSMENT RULES:
- intent_clarity=high:  know exactly what they want (price check, news, explanation, etc.)
- intent_clarity=medium: direction is clear but one key detail is missing
- intent_clarity=low:   too vague — could be anything

- asset_resolved=yes:        a specific stock/company is known or can be inferred
- asset_resolved=not_needed: purely conceptual, no asset required
- asset_resolved=no:         seems market-related but no specific asset identified

- ready=true ONLY when intent_clarity=high AND (asset_resolved=yes OR not_needed)

EXPERT PATH: If the user gives a precise query (e.g. "NVDA 30d momentum"), set ready=true \
immediately. Do not ask unnecessary questions.

NOVICE PATH: Ask one warm, plain-English question at a time. Mention what the system can \
do if that helps orient them. Never re-ask something already answered in the history.

CONTEXT RESOLUTION (critical): Users often refer back to stocks discussed earlier using \
pronouns or vague phrases — "it", "that stock", "the data", "compare it with X", \
"now do the same for Y", "what about its earnings?". \
Always scan the conversation history to resolve these implicit references. \
If a previous turn discussed TSLA and the user now says "compare the data with Apple", \
the ticker field must contain BOTH "TSLA, AAPL" — not just AAPL. \
Populate ticker and/or company_name using history context whenever the current message \
alone is ambiguous. Never ask the user to repeat information already in the history.

When generating clarifying_question, be natural and friendly. Examples:
- "Are you looking to check how a specific stock is performing, or would you like me to \
explain a financial concept?"
- "Which company are you interested in? Just give me the name — I'll look up the ticker \
for you."
- "What aspect interests you most: recent price movement, key metrics like P/E ratio, or \
the latest news?"
"""

# Tool definition — forces Sonnet to produce structured output every turn
_ASSESS_TOOL = {
    "name": "assess_query",
    "description": "Assess the clarity and completeness of the user's financial query.",
    "input_schema": {
        "type": "object",
        "properties": {
            "intent_clarity": {
                "type": "string",
                "enum": ["high", "medium", "low"],
                "description": "How clearly the user has expressed what they want to know.",
            },
            "asset_resolved": {
                "type": "string",
                "enum": ["yes", "no", "not_needed"],
                "description": "Whether a specific stock/asset has been identified.",
            },
            "ready": {
                "type": "boolean",
                "description": "True only when intent_clarity=high AND asset_resolved=yes|not_needed.",
            },
            "inferred_type": {
                "type": "string",
                "enum": ["market", "knowledge", "unclear"],
                "description": "Which system capability this maps to.",
            },
            "company_name": {
                "type": "string",
                "description": (
                    "Company name or natural-language description if mentioned "
                    "(e.g. 'Apple', 'that EV company from China'). Omit if not applicable."
                ),
            },
            "ticker": {
                "type": "string",
                "description": (
                    "Ticker symbol(s) for this query. Include tickers mentioned explicitly "
                    "in the current message AND any tickers that must be inferred from "
                    "conversation history (e.g. if the user says 'compare it with Apple' "
                    "and the previous turn was about TSLA, set this to 'TSLA, AAPL'). "
                    "Separate multiple tickers with commas."
                ),
            },
            "refined_question": {
                "type": "string",
                "description": (
                    "A clean, fully self-contained version of the user's question with all "
                    "pronouns and implicit references resolved using conversation history. "
                    "Must make sense without any prior context "
                    "(e.g. 'Compare TSLA and AAPL performance' not 'compare the data with Apple'). "
                    "Populated when ready=true."
                ),
            },
            "clarifying_question": {
                "type": "string",
                "description": "The single next question to ask the user. Populated when ready=false.",
            },
        },
        "required": ["intent_clarity", "asset_resolved", "ready", "inferred_type"],
    },
}


def _build_messages(
    history_summary: str | None,
    history: list[dict],
    current_message: str,
) -> list[dict]:
    messages: list[dict] = []

    if history_summary:
        # Inject summary as a synthetic exchange so the model has prior context
        messages.append({
            "role": "user",
            "content": f"[Summary of earlier conversation: {history_summary}]",
        })
        messages.append({
            "role": "assistant",
            "content": "Understood — I have context from our earlier exchange.",
        })

    messages.extend(history)
    messages.append({"role": "user", "content": current_message})
    return messages


async def handle_chat(
    message: str,
    history: list[dict],
    history_summary: str | None = None,
) -> dict:
    """
    Multi-turn query understanding handler.

    Returns a dict with:
      type="clarify"  → {message: clarifying question, context_summary: None}
      type="ready"    → {message: final answer, query_type, ticker, refined_question, context_summary}
    """
    client = _get_client()
    messages = _build_messages(history_summary, history, message)

    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=_SYSTEM_PROMPT,
        tools=[_ASSESS_TOOL],
        tool_choice={"type": "any"},   # force tool use every turn
        messages=messages,
    )

    # Extract the structured assessment
    assessment: dict | None = None
    for block in response.content:
        if block.type == "tool_use" and block.name == "assess_query":
            assessment = block.input
            break

    if not assessment:
        # Defensive fallback — should not happen with tool_choice=any
        return {
            "type": "clarify",
            "message": "Could you tell me a bit more about what you're looking for?",
            "context_summary": None,
        }

    # --- Not ready: return the clarifying question ---
    if not assessment.get("ready"):
        return {
            "type": "clarify",
            "message": assessment.get(
                "clarifying_question",
                "Could you give me a bit more detail about what you need?",
            ),
            "context_summary": None,
        }

    # --- Ready: resolve ticker if needed, then route ---
    ticker: str | None = assessment.get("ticker")
    company_name: str | None = assessment.get("company_name")
    inferred_type: str = assessment.get("inferred_type", "knowledge")
    refined_question: str = assessment.get("refined_question") or message

    if inferred_type == "market" and not ticker and company_name:
        ticker = await resolve_ticker(company_name)
        if not ticker:
            # Resolution failed — ask user to clarify rather than silently failing
            return {
                "type": "clarify",
                "message": (
                    f'I couldn\'t find a stock ticker for "{company_name}". '
                    "Could you try the company's full name or provide the ticker symbol directly?"
                ),
                "context_summary": None,
            }

    if inferred_type == "market":
        if not ticker:
            return {
                "type": "clarify",
                "message": "Which company or stock are you asking about?",
                "context_summary": None,
            }

        symbols = _parse_tickers(ticker)

        # ── Multi-stock comparison ──────────────────────────────────────────
        if len(symbols) > 1:
            log.info("[ROUTE] comparison | tickers=%s | question=%r", symbols, refined_question)
            try:
                answer, chart_data = await handle_comparison_query(refined_question, symbols)
            except RuntimeError as e:
                return {"type": "clarify", "message": str(e), "context_summary": None}
            return {
                "type": "ready",
                "message": answer,
                "query_type": "comparison",
                "ticker": ", ".join(symbols),
                "refined_question": refined_question,
                "chart_data": chart_data,
                "context_summary": None,
            }

        # ── Single stock ────────────────────────────────────────────────────
        log.info("[ROUTE] market | ticker=%s | question=%r", symbols[0], refined_question)
        try:
            answer, chart_data = await handle_market_query(refined_question, symbols[0])
        except RuntimeError as e:
            return {
                "type": "clarify",
                "message": str(e),
                "context_summary": None,
            }
        return {
            "type": "ready",
            "message": answer,
            "query_type": "market",
            "ticker": symbols[0],
            "refined_question": refined_question,
            "chart_data": chart_data,
            "context_summary": None,
        }

    # Knowledge path — RAG agent
    log.info("[ROUTE] knowledge | question=%r", refined_question)
    try:
        answer = await handle_knowledge_query(refined_question)
    except RuntimeError as e:
        answer = (
            f"The knowledge base is not available yet ({e}). "
            "Run `python -m rag.build_corpus` then `python -m rag.indexer` to build it."
        )
    return {
        "type": "ready",
        "message": answer,
        "query_type": "knowledge",
        "ticker": None,
        "refined_question": refined_question,
        "context_summary": None,
    }
