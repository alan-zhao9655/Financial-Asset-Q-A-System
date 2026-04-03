"""
Routing accuracy evaluation for the understanding agent.

Measures how reliably the understanding agent classifies queries as:
  - market    (single-ticker market data)
  - comparison (multi-ticker comparison)
  - knowledge  (financial concept from RAG corpus)
  - clarify    (query too vague to route yet)

Methodology:
  - Loads labeled queries from data/routing_labels.json
  - Calls handle_chat() with an empty history (single-turn, no conversation context)
  - Mocks downstream agents (market_agent, rag_agent, comparison_agent) to return
    immediately — we only test routing, not downstream quality
  - Compares returned query_type against expected_type
  - Prints per-category accuracy, overall accuracy, and a confusion matrix

Usage:
    cd financial-qa/backend
    ../../.venv/bin/python ../evaluation/test_routing.py

Requirements:
    ANTHROPIC_API_KEY must be set in the environment or .env file.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

# ---------------------------------------------------------------------------
# Path setup — allow imports from backend/
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")

DATA_FILE = Path(__file__).parent / "data" / "routing_labels.json"


# ---------------------------------------------------------------------------
# Mock downstream agents
# ---------------------------------------------------------------------------

async def _mock_market(question: str, ticker: str):
    return (f"[MOCK market answer for {ticker}]", {})


async def _mock_comparison(question: str, tickers: list[str]):
    return (f"[MOCK comparison answer for {tickers}]", {"type": "comparison", "stocks": []})


async def _mock_knowledge(question: str):
    return "[MOCK knowledge answer]"


# ---------------------------------------------------------------------------
# Evaluation logic
# ---------------------------------------------------------------------------

async def evaluate_single(case: dict) -> dict:
    """Run one labeled query through handle_chat and return the result."""
    from agents.understanding_agent import handle_chat

    with (
        patch("agents.understanding_agent.handle_market_query", new=AsyncMock(side_effect=_mock_market)),
        patch("agents.understanding_agent.handle_comparison_query", new=AsyncMock(side_effect=_mock_comparison)),
        patch("agents.understanding_agent.handle_knowledge_query", new=AsyncMock(side_effect=_mock_knowledge)),
    ):
        result = await handle_chat(
            message=case["query"],
            history=[],
            history_summary=None,
        )

    returned_type = result.get("type")  # "clarify" or "ready"
    query_type    = result.get("query_type")  # "market" | "knowledge" | "comparison" | None

    if returned_type == "clarify":
        predicted = "clarify"
    else:
        predicted = query_type or "unknown"

    expected = case["expected_type"]
    correct  = predicted == expected

    # Ticker check (only for non-knowledge routes)
    ticker_ok = None
    if case.get("expected_ticker") and returned_type == "ready":
        returned_ticker = result.get("ticker", "") or ""
        expected_tickers = set(t.strip().upper() for t in case["expected_ticker"].split(","))
        returned_tickers = set(t.strip().upper() for t in returned_ticker.replace(",", " ").split())
        ticker_ok = expected_tickers == returned_tickers

    return {
        "id":        case["id"],
        "query":     case["query"],
        "expected":  expected,
        "predicted": predicted,
        "correct":   correct,
        "ticker_ok": ticker_ok,
        "note":      case.get("note", ""),
    }


async def run_evaluation():
    cases = json.loads(DATA_FILE.read_text())
    print(f"Running routing evaluation on {len(cases)} labeled queries...\n")

    results = []
    for i, case in enumerate(cases):
        print(f"  [{i+1:02d}/{len(cases)}] {case['id']}: {case['query'][:60]}", end=" ... ", flush=True)
        result = await evaluate_single(case)
        mark = "✓" if result["correct"] else "✗"
        print(mark)
        results.append(result)

    # ---------------------------------------------------------------------------
    # Aggregate metrics
    # ---------------------------------------------------------------------------
    categories = ["market", "comparison", "knowledge", "clarify"]
    label_set  = sorted({r["expected"] for r in results})

    total   = len(results)
    correct = sum(1 for r in results if r["correct"])

    print(f"\n{'='*60}")
    print(f"OVERALL ACCURACY: {correct}/{total} = {correct/total*100:.1f}%")
    print(f"{'='*60}")

    # Per-category accuracy
    print("\nPer-category accuracy:")
    for cat in label_set:
        cat_results = [r for r in results if r["expected"] == cat]
        cat_correct = sum(1 for r in cat_results if r["correct"])
        if cat_results:
            print(f"  {cat:<12}: {cat_correct}/{len(cat_results)} = {cat_correct/len(cat_results)*100:.1f}%")

    # Ticker accuracy (only cases with expected_ticker)
    ticker_results = [r for r in results if r["ticker_ok"] is not None]
    if ticker_results:
        ticker_correct = sum(1 for r in ticker_results if r["ticker_ok"])
        print(f"\nTicker accuracy (market/comparison):  {ticker_correct}/{len(ticker_results)} = {ticker_correct/len(ticker_results)*100:.1f}%")

    # Confusion matrix
    print(f"\nConfusion Matrix (rows=expected, cols=predicted):")
    all_cats = sorted({r["expected"] for r in results} | {r["predicted"] for r in results})
    header = f"{'':12}" + "".join(f"{c:>12}" for c in all_cats)
    print(header)
    for exp in all_cats:
        row = f"{exp:<12}"
        for pred in all_cats:
            count = sum(1 for r in results if r["expected"] == exp and r["predicted"] == pred)
            row += f"{count:>12}"
        print(row)

    # Failures
    failures = [r for r in results if not r["correct"]]
    if failures:
        print(f"\nFailed cases ({len(failures)}):")
        for r in failures:
            print(f"  [{r['id']}] expected={r['expected']:12} predicted={r['predicted']:12} | {r['query'][:55]}")
    else:
        print("\nAll cases passed!")


if __name__ == "__main__":
    asyncio.run(run_evaluation())
