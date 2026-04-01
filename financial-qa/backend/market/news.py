"""Fetch recent news headlines for a ticker via yfinance (Yahoo Finance).

Uses yfinance's t.news — same source as the Yahoo Finance website news tab.
No API key or rate limit concerns since it piggybacks on the same yfinance
session already used for price and fundamentals data.
"""

import yfinance as yf
from dataclasses import dataclass
from typing import List


@dataclass
class NewsItem:
    title: str
    url: str
    snippet: str
    published: str


def fetch_news(ticker: str, max_results: int = 5) -> List[NewsItem]:
    """Return up to *max_results* recent news items for *ticker* via Yahoo Finance."""
    items: List[NewsItem] = []
    try:
        t = yf.Ticker(ticker)
        raw = t.news or []
        for article in raw[:max_results]:
            # t.news entries are dicts; content is nested under "content" key in newer yfinance
            content = article.get("content", article)
            title = content.get("title", "")
            # URL: prefer canonicalUrl → clickThroughUrl → empty
            url = (
                (content.get("canonicalUrl") or {}).get("url", "")
                or (content.get("clickThroughUrl") or {}).get("url", "")
                or ""
            )
            snippet = content.get("summary", "") or content.get("description", "")
            pub = content.get("pubDate", "") or content.get("displayTime", "")
            items.append(NewsItem(title=title, url=url, snippet=snippet, published=pub))
    except Exception:
        pass  # return whatever we have on any error

    return items
