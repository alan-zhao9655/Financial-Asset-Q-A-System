"""Prompt templates for the multi-stock comparison agent."""

COMPARISON_SYSTEM_PROMPT = """\
You are a financial analyst assistant. You will receive structured market data \
for multiple stocks and a user question asking to compare them. \
Your job is to compare them clearly and objectively.

STRICT OUTPUT FORMAT:
────────────────────
## Performance Comparison
Compare the price performance of each stock (day change, 7-day, 30-day). \
State which is outperforming and by how much. Use only the provided numbers.

## Fundamentals
Compare valuation metrics: market cap, P/E ratio, dividend yield, 52-week positioning. \
Highlight meaningful differences. Label analytical statements as opinion \
(e.g. "This suggests …").

## Earnings Trend
If quarterly earnings data is available, compare revenue and net income growth \
across the stocks. If data is missing for any stock, state so explicitly.

## Summary
Two to three sentences directly answering the user's question. \
Which stock is stronger on the metrics asked about, and why.
────────────────────

Rules:
- Never hallucinate numbers. Only use the figures in the data blocks below.
- If a metric is not available for a stock, say "data not available".
- Do not recommend buying or selling any stock.
- FORMATTING: Section headers must use exactly '## ' (two hashes + space).
"""


def _fmt(v, suffix="", decimals=2, na="N/A"):
    if v is None:
        return na
    return f"{v:.{decimals}f}{suffix}"


def _fmt_large(v, na="N/A"):
    if v is None:
        return na
    if abs(v) >= 1e12:
        return f"{v / 1e12:.2f}T"
    if abs(v) >= 1e9:
        return f"{v / 1e9:.2f}B"
    if abs(v) >= 1e6:
        return f"{v / 1e6:.2f}M"
    return str(int(v))


def build_comparison_prompt(
    question: str,
    stocks: list[tuple],   # list of (StockData, MarketMetrics)
) -> str:
    blocks = []
    for data, metrics in stocks:
        earnings_lines = []
        for r in (data.quarterly_earnings or []):
            rev = _fmt_large(r.get("revenue"))
            ni  = _fmt_large(r.get("net_income"))
            earnings_lines.append(f"    {r['period']}  Revenue: {rev}  Net Income: {ni}")
        earnings_block = "\n".join(earnings_lines) or "    Data not available."

        block = f"""\
=== {data.ticker} ({data.company_name}) ===
Currency       : {data.currency}
Sector         : {data.sector or 'N/A'}

--- Price ---
Current price  : {_fmt(metrics.current_price, f' {data.currency}')}
Day change     : {_fmt(metrics.day_change_pct, '%')}
7-day change   : {_fmt(metrics.change_7d_pct, '%')}  [{metrics.trend_7d}]
30-day change  : {_fmt(metrics.change_30d_pct, '%')}  [{metrics.trend_30d}]

--- Range ---
52-week high   : {_fmt(metrics.price_52w_high, f' {data.currency}')}  ({_fmt(abs(metrics.pct_from_52w_high), '%')} {'below' if metrics.pct_from_52w_high < 0 else 'above'} high)
52-week low    : {_fmt(metrics.price_52w_low, f' {data.currency}')}

--- Fundamentals ---
Market cap     : {_fmt_large(data.market_cap)}
P/E ratio      : {_fmt(data.pe_ratio, na='N/A')}
Dividend yield : {_fmt(data.dividend_yield, '%', na='N/A') if data.dividend_yield else 'N/A'}

--- Quarterly Earnings (most recent first) ---
{earnings_block}
=== END {data.ticker} ===
"""
        blocks.append(block)

    return "\n\n".join(blocks) + f"\n\nUser question: {question}"
