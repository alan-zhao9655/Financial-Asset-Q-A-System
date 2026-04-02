"""yfinance wrapper — fetches price history and stock metadata."""

import warnings
import yfinance as yf
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional

# yfinance 0.2.66 uses pd.Timestamp.utcnow() internally, which is deprecated
# in pandas 4. The warning comes from yfinance's own code — suppress it here
# until yfinance ships a fix upstream.
warnings.filterwarnings(
    "ignore",
    message="Timestamp.utcnow is deprecated",
    category=FutureWarning,
)

# yfinance 0.2.66+ uses curl_cffi internally to impersonate Chrome at the TLS
# level — do not pass a custom session; let yfinance handle the connection.
#
# Data source priority:
#   1. t.info  — canonical Yahoo Finance values, matches the website exactly.
#                Reliable now that curl_cffi handles TLS impersonation.
#   2. t.fast_info — fallback only. Returns float32 values (precision noise)
#                    and an incorrect previous_close in some versions; only
#                    used if t.info is unavailable.
#   3. t.history()  — absolute fallback for price/range derivation.


@dataclass
class StockData:
    ticker: str
    company_name: str
    currency: str
    current_price: float
    previous_close: float
    market_cap: Optional[float]
    pe_ratio: Optional[float]
    dividend_yield: Optional[float]
    fifty_two_week_high: float
    fifty_two_week_low: float
    sector: Optional[str]
    industry: Optional[str]
    # Daily OHLCV history, sorted oldest → newest
    history: pd.DataFrame = field(default_factory=pd.DataFrame)
    # Quarterly income statement rows (up to 4 most recent quarters)
    # Each entry: {"period": "2024-12-31", "revenue": 1.2e11, "net_income": 3.6e10}
    quarterly_earnings: list[dict] = field(default_factory=list)
    # Serialised OHLCV for charting — list of dicts with keys:
    # time (YYYY-MM-DD), open, high, low, close, volume
    price_history_ohlcv: list[dict] = field(default_factory=list)


def fetch_stock_data(ticker: str, period: str = "3mo") -> StockData:
    """
    Fetch stock info and price history for *ticker*.

    Args:
        ticker: e.g. "AAPL", "BABA"
        period: yfinance period string — "1mo", "3mo", "6mo", "1y", etc.

    Returns:
        StockData dataclass with metadata and a 'history' DataFrame whose
        columns include Open, High, Low, Close, Volume.
    """
    t = yf.Ticker(ticker)

    # --- Price history (always fetched) ---
    hist = t.history(period=period)
    if hist.empty:
        raise ValueError(f"No price history found for ticker '{ticker}' — check the symbol.")
    hist = hist.sort_index()

    # --- t.info — primary source, matches Yahoo Finance website exactly ---
    info: dict = {}
    try:
        raw = t.info
        if raw and len(raw) > 5:
            info = raw
    except Exception:
        pass

    def _get(key, default=None):
        v = info.get(key)
        return v if v is not None else default

    # --- t.fast_info — fallback when t.info is unavailable ---
    # Note: fast_info.previous_close is unreliable (wrong value in 0.2.66);
    # fast_info prices carry float32 precision noise. Use only if t.info failed.
    fi = None
    if not info:
        try:
            fi = t.fast_info
        except Exception:
            pass

    def _fi(attr, default=None):
        if fi is None:
            return default
        try:
            v = getattr(fi, attr)
            return v if v is not None else default
        except AttributeError:
            return default

    # --- Assemble StockData ---
    current_price = (
        _get("currentPrice")
        or _get("regularMarketPrice")
        or _fi("last_price")
        or float(hist["Close"].iloc[-1])
    )
    previous_close = (
        _get("previousClose")
        or _get("regularMarketPreviousClose")
        # intentionally skip fast_info.previous_close — returns wrong value
        or float(hist["Close"].iloc[-2]) if len(hist) > 1 else current_price
    )
    week52_high = (
        _get("fiftyTwoWeekHigh")
        or _fi("year_high")
        or float(hist["High"].max())
    )
    week52_low = (
        _get("fiftyTwoWeekLow")
        or _fi("year_low")
        or float(hist["Low"].min())
    )

    # --- Quarterly earnings (up to 4 most recent quarters) ---
    quarterly_earnings: list[dict] = []
    try:
        stmt = t.quarterly_income_stmt
        if stmt is not None and not stmt.empty:
            # Columns are period end-dates (newest first); rows are line items
            eps_info = info.get("trailingEps")
            for col in list(stmt.columns)[:4]:
                period_str = col.strftime("%Y-%m-%d") if hasattr(col, "strftime") else str(col)
                revenue = stmt.loc["Total Revenue", col] if "Total Revenue" in stmt.index else None
                net_income = stmt.loc["Net Income", col] if "Net Income" in stmt.index else None
                quarterly_earnings.append({
                    "period": period_str,
                    "revenue": float(revenue) if revenue is not None and not pd.isna(revenue) else None,
                    "net_income": float(net_income) if net_income is not None and not pd.isna(net_income) else None,
                })
    except Exception:
        pass

    # --- Serialise OHLCV for the frontend chart ---
    price_history_ohlcv: list[dict] = []
    for ts, row in hist.iterrows():
        date_str = ts.strftime("%Y-%m-%d") if hasattr(ts, "strftime") else str(ts)[:10]
        price_history_ohlcv.append({
            "time":   date_str,
            "open":   round(float(row["Open"]),   4),
            "high":   round(float(row["High"]),   4),
            "low":    round(float(row["Low"]),    4),
            "close":  round(float(row["Close"]),  4),
            "volume": int(row["Volume"]),
        })

    return StockData(
        ticker=ticker.upper(),
        company_name=_get("longName", ticker.upper()),
        currency=_get("currency") or _fi("currency") or "USD",
        current_price=float(current_price),
        previous_close=float(previous_close),
        market_cap=_get("marketCap") or _fi("market_cap"),
        pe_ratio=_get("trailingPE"),
        dividend_yield=_get("dividendYield"),
        fifty_two_week_high=float(week52_high),
        fifty_two_week_low=float(week52_low),
        sector=_get("sector"),
        industry=_get("industry"),
        history=hist,
        quarterly_earnings=quarterly_earnings,
        price_history_ohlcv=price_history_ohlcv,
    )
