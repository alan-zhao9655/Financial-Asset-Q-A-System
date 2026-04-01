"""Prompt templates for the market data agent."""

MARKET_SYSTEM_PROMPT = """\
You are a financial analyst assistant. You will receive structured market data \
for a stock and a user question. Your job is to answer the question accurately \
and clearly.

STRICT OUTPUT FORMAT:
────────────────────
## Objective Data
List the relevant raw numbers directly from the provided data. \
Do NOT interpret or editorialize here — only facts.

## Analysis
Interpret the numbers. Explain trends, risks, and context. \
Be balanced: acknowledge both positive and negative signals. \
Clearly label any statement that is your analytical opinion (e.g., "This suggests …").

## Summary
One or two sentences directly answering the user's question.
────────────────────

Rules:
- Never hallucinate numbers. Only use the figures provided in the data block.
- If a metric is not available, say "data not available" rather than guessing.
- Do not give personalised investment advice or recommend buying/selling.
- FORMATTING: Section headers must use exactly '## ' (two hashes + space). \
  Never use # or ### or bold text as a substitute for section headers.
"""


def build_market_prompt(
    ticker: str,
    company_name: str,
    currency: str,
    current_price: float,
    day_change_pct: float,
    change_7d_pct,
    change_30d_pct,
    trend_7d: str,
    trend_30d: str,
    biggest_gain_pct: float,
    biggest_gain_date: str,
    biggest_loss_pct: float,
    biggest_loss_date: str,
    price_52w_high: float,
    price_52w_low: float,
    pct_from_52w_high: float,
    pct_from_52w_low: float,
    avg_volume_30d,
    market_cap,
    pe_ratio,
    dividend_yield,
    sector,
    industry,
    news_snippets: list[str],
    user_question: str,
    quarterly_earnings: list[dict] | None = None,
) -> str:
    def _fmt_earnings(rows):
        if not rows:
            return "  Data not available."
        lines = []
        for r in rows:
            rev = fmt_large(r.get("revenue")) if r.get("revenue") else "N/A"
            ni  = fmt_large(r.get("net_income")) if r.get("net_income") else "N/A"
            lines.append(f"  {r['period']}  Revenue: {rev}  Net Income: {ni}")
        return "\n".join(lines)

    def fmt(v, suffix="", decimals=2, na="N/A"):
        if v is None:
            return na
        return f"{v:.{decimals}f}{suffix}"

    def fmt_large(v, na="N/A"):
        if v is None:
            return na
        if v >= 1e12:
            return f"{v/1e12:.2f}T"
        if v >= 1e9:
            return f"{v/1e9:.2f}B"
        if v >= 1e6:
            return f"{v/1e6:.2f}M"
        return str(int(v))

    news_block = "\n".join(
        f"  [{i+1}] {s}" for i, s in enumerate(news_snippets)
    ) or "  No recent news available."

    return f"""\
=== MARKET DATA BLOCK FOR {ticker} ({company_name}) ===
Currency       : {currency}
Sector         : {sector or 'N/A'}
Industry       : {industry or 'N/A'}

--- Price ---
Current price  : {fmt(current_price, f' {currency}')}
Day change     : {fmt(day_change_pct, '%')}
7-day change   : {fmt(change_7d_pct, '%')}  [{trend_7d}]
30-day change  : {fmt(change_30d_pct, '%')}  [{trend_30d}]

--- Range ---
52-week high   : {fmt(price_52w_high, f' {currency}')}  (currently {fmt(abs(pct_from_52w_high), '%')} {'below' if pct_from_52w_high < 0 else 'above'} high)
52-week low    : {fmt(price_52w_low, f' {currency}')}  (currently {fmt(pct_from_52w_low, '%')} above low)

--- Volatility ---
Biggest 1-day gain : {fmt(biggest_gain_pct, '%')} on {biggest_gain_date}
Biggest 1-day loss : {fmt(biggest_loss_pct, '%')} on {biggest_loss_date}

--- Fundamentals ---
Market cap     : {fmt_large(market_cap)}
P/E ratio      : {fmt(pe_ratio, na='N/A')}
Dividend yield : {fmt(dividend_yield, '%', na='N/A') if dividend_yield else 'N/A'}
Avg volume (30d): {fmt_large(avg_volume_30d)}

--- Quarterly Earnings (most recent first) ---
{_fmt_earnings(quarterly_earnings)}
--- Recent News ---
{news_block}
=== END OF DATA BLOCK ===

User question: {user_question}
"""
