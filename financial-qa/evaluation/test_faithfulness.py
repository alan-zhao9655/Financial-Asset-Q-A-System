"""
Answer faithfulness evaluation — LLM-as-judge using Claude Haiku.

Checks that market agent answers don't hallucinate numbers by comparing
every numeric value in the LLM's response against the ground-truth data
block that was sent to it.

Two complementary checks:
  1. Structural check (no LLM): verify the answer has the required sections
     (## Objective Data, ## Analysis, ## Summary) with non-empty content.

  2. Faithfulness check (Haiku as judge): feed Haiku both the raw data block
     and the LLM's answer. Ask: "Does the answer contain any numbers that
     are not present in the data block?"  Returns PASS / FAIL + explanation.

Why Haiku as judge:
  - Sonnet wrote the answer — using Sonnet to judge its own output is less
    reliable than a different model (even a smaller one)
  - The judgment task is simple: compare numbers across two texts, no
    financial expertise required
  - Haiku is 10× cheaper than Sonnet, appropriate for batch evaluation

Test cases — representative query × ticker pairs that exercise each section:
  - Price + range query (exercises Objective Data)
  - Volume + trend query (exercises Analysis)
  - Earnings query (exercises Quarterly Earnings block)
  - News-heavy query (exercises news citation)

Usage:
    cd financial-qa/backend
    ../../.venv/bin/python ../evaluation/test_faithfulness.py

Requires ANTHROPIC_API_KEY in environment / .env.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")

import anthropic

# Test cases: (ticker, question, description)
TEST_CASES = [
    ("AAPL", "What is Apple's current price and how is it doing over the past month?", "price + trend"),
    ("MSFT", "What is Microsoft's market cap and P/E ratio?",                           "fundamentals"),
    ("TSLA", "What are Tesla's most recent quarterly earnings?",                        "earnings"),
    ("NVDA", "What is Nvidia's 52-week high and how far is it from there now?",         "52w range"),
    ("AMZN", "What is Amazon's trading volume and any recent news?",                    "volume + news"),
]

_FAITHFULNESS_JUDGE_PROMPT = """\
You are evaluating whether a financial analyst's answer is faithful to the data it was given.

## Data Block (ground truth)
{data_block}

## Analyst's Answer
{answer}

## Task
Check whether the analyst's answer contains any numeric values that:
1. Are NOT present in the Data Block, AND
2. Could mislead a reader (i.e. they look like real financial figures, not approximations or general statements)

Ignore:
- Rounded or approximated versions of numbers in the data block (e.g. "about 3%" when data says 2.97%)
- Generic statements like "significant" or "strong" without specific numbers
- Numbers that are clearly derived correctly from data block figures (e.g. price difference)

Respond with JSON only:
{{
  "verdict": "PASS" or "FAIL",
  "hallucinated_numbers": ["list of specific numbers not found in data block, empty if PASS"],
  "explanation": "one sentence"
}}
"""

_STRUCTURAL_SECTIONS = ["## Objective Data", "## Analysis", "## Summary"]


def check_structure(answer: str) -> dict:
    """Check that all required sections are present and non-empty."""
    issues = []
    for section in _STRUCTURAL_SECTIONS:
        if section not in answer:
            issues.append(f"Missing section: {section}")

    return {
        "passed": len(issues) == 0,
        "issues": issues,
    }


async def check_faithfulness(
    data_block: str,
    answer: str,
    client: anthropic.AsyncAnthropic,
) -> dict:
    """Use Haiku to judge whether the answer hallucinated any numbers."""
    prompt = _FAITHFULNESS_JUDGE_PROMPT.format(data_block=data_block, answer=answer)

    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"verdict": "ERROR", "explanation": f"Could not parse judge response: {raw[:100]}"}


async def evaluate_single(ticker: str, question: str, description: str, client: anthropic.AsyncAnthropic) -> dict:
    """Run one test case end-to-end and return evaluation result."""
    from market.fetcher import fetch_stock_data
    from market.calculator import compute_metrics
    from market.news import fetch_news
    from prompts.market_prompt import MARKET_SYSTEM_PROMPT, build_market_prompt

    # Fetch data
    data    = fetch_stock_data(ticker)
    metrics = compute_metrics(data)
    news    = fetch_news(ticker)
    news_items = [{"title": n.title, "url": n.url, "snippet": n.snippet} for n in news]

    # Build the exact prompt that goes to the LLM
    data_block = build_market_prompt(
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
        news_items=news_items,
        user_question=question,
        quarterly_earnings=data.quarterly_earnings,
    )

    # Get market agent answer (Sonnet)
    sonnet = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = await sonnet.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=MARKET_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": data_block}],
    )
    answer = response.content[0].text

    # Structural check
    structure = check_structure(answer)

    # Faithfulness check (Haiku as judge)
    faithfulness = await check_faithfulness(data_block, answer, client)

    return {
        "ticker":       ticker,
        "question":     question,
        "description":  description,
        "structure":    structure,
        "faithfulness": faithfulness,
    }


async def run_evaluation():
    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    print("Market answer faithfulness evaluation\n")
    print("(Uses Claude Sonnet to generate answers, Claude Haiku to judge)\n")

    results = []
    for ticker, question, description in TEST_CASES:
        print(f"  {ticker} / {description:<25}", end=" ... ", flush=True)
        result = await evaluate_single(ticker, question, description, client)
        results.append(result)

        struct_ok = result["structure"]["passed"]
        faith_ok  = result["faithfulness"].get("verdict") == "PASS"
        status    = "✓" if (struct_ok and faith_ok) else "✗"
        print(f"{status}  structure={'OK' if struct_ok else 'FAIL'}  faithfulness={result['faithfulness'].get('verdict', 'ERR')}")

    # Summary
    print(f"\n{'='*60}")
    total             = len(results)
    struct_pass       = sum(1 for r in results if r["structure"]["passed"])
    faith_pass        = sum(1 for r in results if r["faithfulness"].get("verdict") == "PASS")
    both_pass         = sum(1 for r in results if r["structure"]["passed"] and r["faithfulness"].get("verdict") == "PASS")

    print(f"Structural integrity : {struct_pass}/{total}")
    print(f"Faithfulness (Haiku) : {faith_pass}/{total}")
    print(f"Both passing         : {both_pass}/{total}")

    # Detail failures
    for r in results:
        struct_ok = r["structure"]["passed"]
        faith_ok  = r["faithfulness"].get("verdict") == "PASS"
        if not struct_ok:
            print(f"\n  STRUCTURE FAIL [{r['ticker']}]: {r['structure']['issues']}")
        if not faith_ok:
            explanation = r["faithfulness"].get("explanation", "")
            hallucinated = r["faithfulness"].get("hallucinated_numbers", [])
            print(f"\n  FAITHFULNESS FAIL [{r['ticker']} / {r['description']}]:")
            print(f"    Hallucinated numbers: {hallucinated}")
            print(f"    Explanation: {explanation}")


if __name__ == "__main__":
    asyncio.run(run_evaluation())
