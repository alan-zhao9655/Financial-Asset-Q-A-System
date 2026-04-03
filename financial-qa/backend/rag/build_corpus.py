"""Wikipedia corpus fetcher for the financial knowledge base.

Pulls ~80 financial concept articles from Wikipedia across multiple categories,
converts each to clean markdown with section headers preserved, and saves them.

Usage:
    python -m rag.build_corpus          # fetch all articles
    python -m rag.build_corpus --list   # print article list and exit
"""

import re
import sys
import time
import argparse
from pathlib import Path

import wikipediaapi

# Ensure this points to your actual data directory
DOCUMENTS_DIR = Path("rag/data/documents")

# ---------------------------------------------------------------------------
# Categorized Article List — { "Category": [("Wikipedia_Title", "filename.md")] }
# ---------------------------------------------------------------------------
CATEGORIZED_ARTICLES = {
    "Corporate Finance & Accounting": [
        ("Revenue", "revenue.md"),
        ("Net income", "net_income.md"),
        ("Gross profit", "gross_profit.md"),
        ("Operating margin", "operating_margin.md"),
        ("Balance sheet", "balance_sheet.md"),
        ("Income statement", "income_statement.md"),
        ("Cash flow statement", "cash_flow_statement.md"),
        ("EBITDA", "ebitda.md"),
        ("Free cash flow", "free_cash_flow.md"),
        ("Capital expenditure", "capex.md"),
        ("Working capital", "working_capital.md"),
        ("Return on equity", "roe.md"),
        ("Return on assets", "roa.md"),
    ],
    "Valuation & Metrics": [
        ("Price–earnings ratio", "pe_ratio.md"),
        ("Price-to-book ratio", "pb_ratio.md"),
        ("Dividend yield", "dividend_yield.md"),
        ("Earnings per share", "earnings_per_share.md"),
        ("Market capitalization", "market_cap.md"),
        ("Enterprise value", "enterprise_value.md"),
        ("Discounted cash flow", "dcf_valuation.md"),
        ("Weighted average cost of capital", "wacc.md"),
    ],
    "Financial Markets & Instruments": [
        ("Stock", "stock.md"),
        ("Bond (finance)", "bonds.md"),
        ("Exchange-traded fund", "etfs.md"),
        ("Mutual fund", "mutual_funds.md"),
        ("Index fund", "index_funds.md"),
        ("Hedge fund", "hedge_funds.md"),
        ("Derivative (finance)", "derivatives.md"),
        ("Options (finance)", "options.md"),
        ("Futures contract", "futures.md"),
        ("Commodity market", "commodities.md"),
        ("Cryptocurrency", "cryptocurrency.md"),
    ],
    "Trading Mechanics & Strategies": [
        ("Order (exchange)", "market_orders.md"),
        ("Short (finance)", "short_selling.md"),
        ("Margin (finance)", "margin_trading.md"),
        ("Stock split", "stock_splits.md"),
        ("Dividend", "dividends.md"),
        ("Dollar cost averaging", "dollar_cost_averaging.md"),
        ("Diversification (finance)", "portfolio_diversification.md"),
        ("Market trend", "bear_bull_markets.md"),
        ("52-week high", "52_week_high_low.md"),
        ("Relative strength index", "rsi.md"),
        ("Moving average", "moving_averages.md"),
        ("MACD", "macd.md"),
        ("Volatility (finance)", "volatility.md"),
    ],
    "Macroeconomics & Banking": [
        ("Inflation", "inflation.md"),
        ("Interest rate", "interest_rates.md"),
        ("Gross domestic product", "gdp.md"),
        ("Central bank", "central_banks.md"),
        ("Quantitative easing", "quantitative_easing.md"),
        ("Recession", "recession.md"),
        ("Federal Reserve", "federal_reserve.md"),
    ]
}

# Sections to skip — boilerplate that adds noise without value for Q&A
_SKIP_SECTIONS = {
    "see also", "references", "further reading", "external links",
    "notes", "bibliography", "footnotes", "citations", "literature",
}

# Max chars per section to keep (avoids indexing enormous tangential sections)
_MAX_SECTION_CHARS = 6000

def _clean_text(text: str) -> str:
    """Remove citation markers and normalise whitespace."""
    text = re.sub(r"\[\d+\]", "", text)          # [1], [23], etc.
    text = re.sub(r"\[citation needed\]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\n{3,}", "\n\n", text)        # collapse excessive blank lines
    return text.strip()

def _section_to_markdown(section, depth: int = 2) -> str:
    """Recursively convert a wikipediaapi Section to markdown text."""
    if section.title.lower() in _SKIP_SECTIONS:
        return ""

    header = "#" * depth + " " + section.title
    body   = _clean_text(section.text)

    # Truncate very long sections (tangential detail)
    if len(body) > _MAX_SECTION_CHARS:
        body = body[:_MAX_SECTION_CHARS] + "\n\n*(section truncated for brevity)*"

    parts = []
    if body:
        parts.append(f"{header}\n\n{body}")
    else:
        parts.append(header)

    for subsection in section.sections:
        md = _section_to_markdown(subsection, depth + 1)
        if md:
            parts.append(md)

    return "\n\n".join(parts)

def fetch_article(wiki: wikipediaapi.Wikipedia, title: str, filename: str) -> bool:
    """Fetch one Wikipedia article and write it as a markdown file."""
    page = wiki.page(title)

    if not page.exists():
        print(f"  [SKIP] '{title}' — page not found on Wikipedia")
        return False

    lines = [
        f"# {page.title}",
        "",
        f"> **Source:** [Wikipedia — {page.title}]({page.fullurl})",
        f"> **Category:** Assigned during local extraction",
        "",
        _clean_text(page.summary),
    ]

    for section in page.sections:
        md = _section_to_markdown(section, depth=2)
        if md:
            lines.append("")
            lines.append(md)

    content = "\n".join(lines)
    out_path = DOCUMENTS_DIR / filename
    out_path.write_text(content, encoding="utf-8")
    print(f"  [OK]   {filename:<25} ({len(content):,} chars)")
    return True

def build_corpus():
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

    wiki = wikipediaapi.Wikipedia(
        language="en",
        user_agent="FinancialQASystem/1.0 (educational project; contact: local)",
    )

    total_articles = sum(len(articles) for articles in CATEGORIZED_ARTICLES.values())
    print(f"Fetching {total_articles} Wikipedia articles → {DOCUMENTS_DIR}\n")
    
    ok = 0
    for category, articles in CATEGORIZED_ARTICLES.items():
        print(f"\n--- {category} ---")
        for title, filename in articles:
            if fetch_article(wiki, title, filename):
                ok += 1
            # Polite rate limiting to avoid Wikipedia API bans
            time.sleep(0.5) 

    print(f"\nDone: {ok}/{total_articles} articles saved.")
    if ok < total_articles:
        print("Re-run to retry failed articles, or check the titles against Wikipedia.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the financial knowledge base corpus.")
    parser.add_argument("--list", action="store_true", help="Print article list and exit")
    args = parser.parse_args()

    if args.list:
        for category, articles in CATEGORIZED_ARTICLES.items():
            print(f"\n[{category}]")
            for title, filename in articles:
                print(f"  {filename:<25} {title}")
        sys.exit(0)

    build_corpus()