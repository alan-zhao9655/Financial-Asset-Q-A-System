"""
Quick smoke-test for the data layer (no LLM calls).
Run from the backend/ directory:
    python test_market.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from market.fetcher import fetch_stock_data
from market.calculator import compute_metrics

TICKER = "BABA"


def main():
    print(f"Fetching data for {TICKER} …")
    data = fetch_stock_data(TICKER, period="3mo")

    print(f"\n{'='*50}")
    print(f"  {data.company_name} ({data.ticker})")
    print(f"{'='*50}")
    print(f"  Currency      : {data.currency}")
    print(f"  Sector        : {data.sector}")
    print(f"  Industry      : {data.industry}")
    print(f"  Market Cap    : {data.market_cap:,.0f}" if data.market_cap else "  Market Cap    : N/A")
    print(f"  P/E Ratio     : {data.pe_ratio}" if data.pe_ratio else "  P/E Ratio     : N/A")
    print(f"  History rows  : {len(data.history)}")
    print()

    print("Computing metrics …")
    m = compute_metrics(data)

    print(f"\n{'='*50}")
    print("  COMPUTED METRICS")
    print(f"{'='*50}")
    print(f"  Current price        : {m.current_price} {data.currency}")
    print(f"  Previous close       : {m.previous_close} {data.currency}")
    print(f"  Day change           : {m.day_change_pct:+.2f}%")
    print()
    print(f"  7-day change         : {m.change_7d_pct:+.2f}%  [{m.trend_7d}]" if m.change_7d_pct is not None else "  7-day change         : N/A")
    print(f"  30-day change        : {m.change_30d_pct:+.2f}%  [{m.trend_30d}]" if m.change_30d_pct is not None else "  30-day change        : N/A")
    print()
    print(f"  52-week high         : {m.price_52w_high} ({m.pct_from_52w_high:+.2f}% from current)")
    print(f"  52-week low          : {m.price_52w_low} ({m.pct_from_52w_low:+.2f}% from current)")
    print()
    print(f"  Biggest 1-day gain   : {m.biggest_single_day_gain_pct:+.2f}% on {m.biggest_single_day_gain_date}")
    print(f"  Biggest 1-day loss   : {m.biggest_single_day_loss_pct:+.2f}% on {m.biggest_single_day_loss_date}")
    print()
    print(f"  Avg volume (30d)     : {m.avg_volume_30d:,.0f}" if m.avg_volume_30d else "  Avg volume (30d)     : N/A")
    print()
    print("Done.")


if __name__ == "__main__":
    main()
