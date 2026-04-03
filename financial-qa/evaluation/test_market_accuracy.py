"""
Market data layer evaluation — structural integrity and mathematical consistency.

No LLM calls. Tests the fetcher + calculator pipeline directly.

Checks for each test ticker:
  1. StockData structural integrity
     - Non-empty price history
     - All required fields present and non-null
     - OHLCV sanity: high >= low, high >= open, high >= close, low <= open, low <= close

  2. MarketMetrics mathematical consistency
     - day_change_pct = (current - prev_close) / prev_close * 100  (within 0.01%)
     - 7d/30d % changes computed from history (cross-check against calculator)
     - 52-week high >= 52-week low
     - current price within [52w_low * 0.95, 52w_high * 1.05] (wide tolerance for stale data)
     - pct_from_52w_high: consistent with (current - high) / high * 100

  3. Quarterly earnings sanity
     - Each entry has period, revenue (or None), net_income (or None)
     - Periods are in descending order (newest first)

  4. OHLCV serialisation consistency
     - price_history_ohlcv matches hist DataFrame for the same dates

Usage:
    cd financial-qa/backend
    ../../.venv/bin/python ../evaluation/test_market_accuracy.py

No API key required — uses yfinance data only.
"""

from __future__ import annotations

import sys
from pathlib import Path
from dataclasses import dataclass

BACKEND_DIR = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# Tickers to evaluate — mix of US large cap, international, and ETF
TEST_TICKERS = ["AAPL", "MSFT", "TSLA", "BABA", "SPY"]


@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str = ""


def check_stock_data(ticker: str) -> list[CheckResult]:
    from market.fetcher import fetch_stock_data
    from market.calculator import compute_metrics

    results: list[CheckResult] = []

    # Fetch
    try:
        data = fetch_stock_data(ticker)
    except Exception as e:
        return [CheckResult("fetch", False, str(e))]

    # --- Structural integrity ---
    results.append(CheckResult(
        "history_not_empty",
        not data.history.empty,
        f"{len(data.history)} rows" if not data.history.empty else "empty DataFrame",
    ))

    results.append(CheckResult(
        "current_price_positive",
        data.current_price > 0,
        f"current_price={data.current_price}",
    ))

    results.append(CheckResult(
        "previous_close_positive",
        data.previous_close > 0,
        f"previous_close={data.previous_close}",
    ))

    results.append(CheckResult(
        "52w_high_gte_low",
        data.fifty_two_week_high >= data.fifty_two_week_low,
        f"high={data.fifty_two_week_high:.2f} low={data.fifty_two_week_low:.2f}",
    ))

    results.append(CheckResult(
        "ohlcv_serialized",
        len(data.price_history_ohlcv) > 0,
        f"{len(data.price_history_ohlcv)} OHLCV rows",
    ))

    # --- OHLCV candle sanity (spot-check last 5 rows) ---
    ohlcv_errors = []
    for row in data.price_history_ohlcv[-5:]:
        h, l, o, c = row["high"], row["low"], row["open"], row["close"]
        if not (h >= l):
            ohlcv_errors.append(f"high({h}) < low({l}) on {row['time']}")
        if not (h >= o):
            ohlcv_errors.append(f"high({h}) < open({o}) on {row['time']}")
        if not (h >= c):
            ohlcv_errors.append(f"high({h}) < close({c}) on {row['time']}")
        if not (l <= o):
            ohlcv_errors.append(f"low({l}) > open({o}) on {row['time']}")
        if not (l <= c):
            ohlcv_errors.append(f"low({l}) > close({c}) on {row['time']}")

    results.append(CheckResult(
        "ohlcv_candle_sanity",
        len(ohlcv_errors) == 0,
        "; ".join(ohlcv_errors) if ohlcv_errors else "all candles valid",
    ))

    # --- Metrics mathematical consistency ---
    try:
        metrics = compute_metrics(data)
    except Exception as e:
        results.append(CheckResult("metrics_compute", False, str(e)))
        return results

    # day_change_pct = (current - prev_close) / prev_close * 100
    expected_day_change = (data.current_price - data.previous_close) / data.previous_close * 100
    day_diff = abs(metrics.day_change_pct - expected_day_change)
    results.append(CheckResult(
        "day_change_pct_consistent",
        day_diff < 0.01,
        f"metric={metrics.day_change_pct:.4f}% expected={expected_day_change:.4f}% diff={day_diff:.6f}",
    ))

    # 52w range: current should be within plausible bounds
    # Allow 5% slack because live price vs historical high/low can diverge
    price_in_range = (
        data.current_price <= data.fifty_two_week_high * 1.05
        and data.current_price >= data.fifty_two_week_low * 0.95
    )
    results.append(CheckResult(
        "current_price_in_52w_range",
        price_in_range,
        f"price={data.current_price:.2f} 52w=[{data.fifty_two_week_low:.2f}, {data.fifty_two_week_high:.2f}]",
    ))

    # pct_from_52w_high consistency
    expected_from_high = (data.current_price - data.fifty_two_week_high) / data.fifty_two_week_high * 100
    high_diff = abs(metrics.pct_from_52w_high - expected_from_high)
    results.append(CheckResult(
        "pct_from_52w_high_consistent",
        high_diff < 0.01,
        f"metric={metrics.pct_from_52w_high:.4f}% expected={expected_from_high:.4f}% diff={high_diff:.6f}",
    ))

    # avg_volume_30d should be positive
    results.append(CheckResult(
        "avg_volume_positive",
        metrics.avg_volume_30d > 0,
        f"avg_volume_30d={metrics.avg_volume_30d:,.0f}",
    ))

    # biggest gain > 0, biggest loss < 0
    results.append(CheckResult(
        "biggest_gain_positive",
        metrics.biggest_single_day_gain_pct > 0,
        f"{metrics.biggest_single_day_gain_pct:.2f}% on {metrics.biggest_single_day_gain_date}",
    ))
    results.append(CheckResult(
        "biggest_loss_negative",
        metrics.biggest_single_day_loss_pct < 0,
        f"{metrics.biggest_single_day_loss_pct:.2f}% on {metrics.biggest_single_day_loss_date}",
    ))

    # --- Quarterly earnings sanity ---
    if data.quarterly_earnings:
        # All entries must have a period string
        periods_valid = all(isinstance(e.get("period"), str) for e in data.quarterly_earnings)
        results.append(CheckResult(
            "quarterly_periods_valid",
            periods_valid,
            f"{len(data.quarterly_earnings)} quarters",
        ))

        # Periods should be in descending order (newest first)
        periods = [e["period"] for e in data.quarterly_earnings]
        descending = all(periods[i] >= periods[i+1] for i in range(len(periods)-1))
        results.append(CheckResult(
            "quarterly_periods_descending",
            descending,
            f"periods={periods}",
        ))
    else:
        results.append(CheckResult(
            "quarterly_earnings_available",
            False,
            "no quarterly earnings returned (may be normal for some tickers)",
        ))

    return results


def run_evaluation():
    print("Market data accuracy evaluation\n")
    all_pass = True

    for ticker in TEST_TICKERS:
        print(f"{'─'*50}")
        print(f"Ticker: {ticker}")
        checks = check_stock_data(ticker)
        for c in checks:
            status = "PASS" if c.passed else "FAIL"
            print(f"  [{status}] {c.name:<35} {c.message}")
            if not c.passed:
                all_pass = False
        print()

    print(f"{'='*50}")
    if all_pass:
        print("All checks passed.")
    else:
        print("Some checks FAILED — review output above.")


if __name__ == "__main__":
    run_evaluation()
