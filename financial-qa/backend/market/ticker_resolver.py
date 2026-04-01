import asyncio
import os
import anthropic
import yfinance as yf

_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


_SYSTEM = (
    "You are a stock ticker resolver. Given a company name, description, or colloquial "
    "reference, respond with ONLY the stock ticker symbol (e.g. AAPL, TSLA, META, NIO). "
    "Examples: 'Apple' → AAPL, 'Zuckerberg company' → META, 'EV company from China' → NIO. "
    "If you cannot determine a specific ticker with confidence, respond with UNKNOWN."
)


def _validate(ticker: str) -> bool:
    """Confirm the ticker exists in yfinance (runs in thread — yfinance is sync)."""
    try:
        hist = yf.Ticker(ticker).history(period="1d")
        return not hist.empty
    except Exception:
        return False


async def resolve_ticker(company_name: str) -> str | None:
    """
    Resolve a company name or natural-language description to a validated ticker.
    Returns the ticker string on success, None if unresolvable or not found in yfinance.
    """
    client = _get_client()

    msg = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=10,
        system=_SYSTEM,
        messages=[{"role": "user", "content": company_name}],
    )

    raw = msg.content[0].text.strip().upper().strip(".")
    if not raw or raw == "UNKNOWN":
        return None

    valid = await asyncio.to_thread(_validate, raw)
    return raw if valid else None
