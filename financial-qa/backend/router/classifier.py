import os
import anthropic

_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


_SYSTEM_PROMPT = """\
You are a query router for a financial Q&A system that has two capabilities:

MARKET: answers questions that require live or recent data — current prices, \
percentage changes, recent news, earnings, volatility, trading volume, or any \
question about how a specific asset has *actually performed*. These questions \
need real-time data fetched from the market.

KNOWLEDGE: answers questions that require explanation of financial concepts, \
definitions, educational content, or general information that does not depend \
on live data — e.g. "what does P/E ratio mean", "how does dollar-cost averaging \
work", "what is a bond".

ROUTING RULES:
- If the question asks about a specific company/ticker's actual behaviour \
(past or present), route to MARKET — even if phrased as "explain why X happened".
- If the question mentions a ticker but asks for live metrics (price, ratio, \
volume, news), route to MARKET.
- If the question is purely conceptual and no live data would change the answer, \
route to KNOWLEDGE.
- When in doubt, prefer MARKET.

Respond with exactly one word: MARKET or KNOWLEDGE.\
"""


async def classify_query(question: str) -> str:
    """Return 'market' or 'knowledge' by asking Haiku to reason about intent."""
    client = _get_client()

    message = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=5,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": question}],
    )

    result = message.content[0].text.strip().upper()
    return "market" if result == "MARKET" else "knowledge"
