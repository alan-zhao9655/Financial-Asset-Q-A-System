"""Comparison agent — fetches multiple tickers in parallel and generates a side-by-side analysis."""

from __future__ import annotations

import asyncio
import logging
from functools import lru_cache

from anthropic import AsyncAnthropic

from market.fetcher import fetch_stock_data
from market.calculator import compute_metrics
from prompts.comparison_prompt import COMPARISON_SYSTEM_PROMPT, build_comparison_prompt

log = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_client() -> AsyncAnthropic:
    return AsyncAnthropic()


async def _fetch_one(ticker: str):
    """Fetch and compute metrics for a single ticker in a thread pool."""
    data    = await asyncio.to_thread(fetch_stock_data, ticker)
    metrics = await asyncio.to_thread(compute_metrics, data)
    return data, metrics


async def handle_comparison_query(question: str, tickers: list[str]) -> tuple[str, dict]:
    """
    Fetch all tickers in parallel, build a comparison answer, and return
    (answer_text, chart_data) where chart_data.type == "comparison".
    """
    log.info("[COMPARISON] fetching tickers=%s", tickers)

    results = await asyncio.gather(
        *[_fetch_one(t) for t in tickers],
        return_exceptions=True,
    )

    stocks      = []   # (StockData, MarketMetrics) — successful fetches only
    chart_stocks = []
    failed      = []

    for ticker, result in zip(tickers, results):
        if isinstance(result, Exception):
            log.warning("[COMPARISON] failed to fetch %s: %s", ticker, result)
            failed.append(ticker)
            continue

        data, metrics = result
        stocks.append((data, metrics))

        chart_stocks.append({
            "ticker":             data.ticker,
            "company_name":       data.company_name,
            "currency":           data.currency,
            "price_history":      data.price_history_ohlcv,
            "quarterly_earnings": data.quarterly_earnings,
            "metrics": {
                "current_price":    metrics.current_price,
                "day_change_pct":   metrics.day_change_pct,
                "change_7d_pct":    metrics.change_7d_pct,
                "change_30d_pct":   metrics.change_30d_pct,
                "price_52w_high":   metrics.price_52w_high,
                "price_52w_low":    metrics.price_52w_low,
                "pct_from_52w_high": metrics.pct_from_52w_high,
                "market_cap":       data.market_cap,
                "pe_ratio":         data.pe_ratio,
                "dividend_yield":   data.dividend_yield,
                "sector":           data.sector,
            },
        })

    if not stocks:
        raise RuntimeError(
            f"Could not fetch market data for any of the requested tickers: {', '.join(failed)}"
        )

    log.info(
        "[COMPARISON] fetched=%s failed=%s",
        [s[0].ticker for s in stocks],
        failed or "none",
    )

    prompt   = build_comparison_prompt(question, stocks)
    client   = _get_client()
    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=COMPARISON_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    chart_data = {
        "type":   "comparison",
        "stocks": chart_stocks,
    }

    return response.content[0].text, chart_data
