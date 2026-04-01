"""Market agent: orchestrates fetch → compute → news → LLM."""

import os
import logging
import anthropic
from market.fetcher import fetch_stock_data
from market.calculator import compute_metrics
from market.news import fetch_news
from prompts.market_prompt import MARKET_SYSTEM_PROMPT, build_market_prompt

log = logging.getLogger(__name__)

_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


async def handle_market_query(question: str, ticker: str) -> str:
    data = fetch_stock_data(ticker)
    metrics = compute_metrics(data)
    news = fetch_news(ticker)
    log.info(
        "[MARKET] ticker=%s | company=%s | price=%s | news=%d | earnings_quarters=%d",
        ticker,
        data.company_name or "N/A",
        metrics.current_price,
        len(news),
        len(data.quarterly_earnings) if data.quarterly_earnings else 0,
    )
    news_snippets = [f"{n.title} — {n.snippet}" for n in news]

    user_content = build_market_prompt(
        ticker=metrics.ticker,
        company_name=data.company_name,
        currency=data.currency,
        current_price=metrics.current_price,
        day_change_pct=metrics.day_change_pct,
        change_7d_pct=metrics.change_7d_pct,
        change_30d_pct=metrics.change_30d_pct,
        trend_7d=metrics.trend_7d,
        trend_30d=metrics.trend_30d,
        biggest_gain_pct=metrics.biggest_single_day_gain_pct,
        biggest_gain_date=metrics.biggest_single_day_gain_date,
        biggest_loss_pct=metrics.biggest_single_day_loss_pct,
        biggest_loss_date=metrics.biggest_single_day_loss_date,
        price_52w_high=metrics.price_52w_high,
        price_52w_low=metrics.price_52w_low,
        pct_from_52w_high=metrics.pct_from_52w_high,
        pct_from_52w_low=metrics.pct_from_52w_low,
        avg_volume_30d=metrics.avg_volume_30d,
        market_cap=data.market_cap,
        pe_ratio=data.pe_ratio,
        dividend_yield=data.dividend_yield,
        sector=data.sector,
        industry=data.industry,
        news_snippets=news_snippets,
        user_question=question,
        quarterly_earnings=data.quarterly_earnings,
    )

    client = _get_client()
    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=MARKET_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )

    return response.content[0].text
