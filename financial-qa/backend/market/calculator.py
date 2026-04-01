"""Pure-Python metrics computation — no LLM calls."""

from dataclasses import dataclass
from typing import Optional
import pandas as pd
from market.fetcher import StockData


@dataclass
class MarketMetrics:
    ticker: str
    current_price: float
    previous_close: float
    day_change_pct: float

    change_7d_pct: Optional[float]
    change_30d_pct: Optional[float]

    trend_7d: str   # "up" | "down" | "flat"
    trend_30d: str

    biggest_single_day_gain_pct: float
    biggest_single_day_gain_date: str
    biggest_single_day_loss_pct: float
    biggest_single_day_loss_date: str

    price_52w_high: float
    price_52w_low: float
    pct_from_52w_high: float
    pct_from_52w_low: float

    avg_volume_30d: Optional[float]


def _pct(new: float, old: float) -> float:
    if old == 0:
        return 0.0
    return round((new - old) / abs(old) * 100, 2)


def _trend_label(pct: Optional[float]) -> str:
    if pct is None:
        return "unknown"
    if pct > 1:
        return "up"
    if pct < -1:
        return "down"
    return "flat"


def compute_metrics(data: StockData) -> MarketMetrics:
    """
    Derive all numeric metrics from a StockData object.
    All computation is arithmetic — no LLM involved.
    """
    hist: pd.DataFrame = data.history.copy()
    closes = hist["Close"]

    # Day change
    day_change = _pct(data.current_price, data.previous_close)

    # 7d / 30d changes (uses trading days in history)
    change_7d = change_30d = None
    if len(closes) >= 6:
        change_7d = _pct(float(closes.iloc[-1]), float(closes.iloc[-6]))
    if len(closes) >= 22:
        change_30d = _pct(float(closes.iloc[-1]), float(closes.iloc[-22]))

    # Biggest single-day moves (% change day-over-day)
    daily_returns = closes.pct_change().dropna() * 100

    gain_idx = daily_returns.idxmax()
    loss_idx = daily_returns.idxmin()

    biggest_gain = round(float(daily_returns[gain_idx]), 2)
    biggest_loss = round(float(daily_returns[loss_idx]), 2)
    gain_date = gain_idx.strftime("%Y-%m-%d") if hasattr(gain_idx, "strftime") else str(gain_idx)
    loss_date = loss_idx.strftime("%Y-%m-%d") if hasattr(loss_idx, "strftime") else str(loss_idx)

    # 52-week positioning
    pct_from_high = _pct(data.current_price, data.fifty_two_week_high)
    pct_from_low = _pct(data.current_price, data.fifty_two_week_low)

    # Average volume (last 30 trading days)
    avg_vol = None
    if "Volume" in hist.columns and len(hist) >= 5:
        avg_vol = round(float(hist["Volume"].iloc[-30:].mean()), 0)

    return MarketMetrics(
        ticker=data.ticker,
        current_price=round(data.current_price, 4),
        previous_close=round(data.previous_close, 4),
        day_change_pct=day_change,
        change_7d_pct=change_7d,
        change_30d_pct=change_30d,
        trend_7d=_trend_label(change_7d),
        trend_30d=_trend_label(change_30d),
        biggest_single_day_gain_pct=biggest_gain,
        biggest_single_day_gain_date=gain_date,
        biggest_single_day_loss_pct=biggest_loss,
        biggest_single_day_loss_date=loss_date,
        price_52w_high=data.fifty_two_week_high,
        price_52w_low=data.fifty_two_week_low,
        pct_from_52w_high=pct_from_high,
        pct_from_52w_low=pct_from_low,
        avg_volume_30d=avg_vol,
    )
