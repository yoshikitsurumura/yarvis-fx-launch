from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd


@dataclass
class RiskConfig:
    per_trade_risk_pct: float = 0.25
    daily_loss_stop_pct: float = 1.0
    max_concurrent_positions: int = 1


def position_size_from_atr(entry_price: float, atr_value: float, atr_k_stop: float,
                           equity: float, per_trade_risk_pct: float) -> float:
    risk_jpy = equity * (per_trade_risk_pct / 100.0)
    stop_distance = atr_k_stop * atr_value
    if stop_distance <= 0:
        return 0.0
    units = risk_jpy / stop_distance
    return max(0.0, units)


def apply_daily_loss_stop(pnl_series: pd.Series, equity_start: float, daily_loss_stop_pct: float) -> pd.Series:
    """
    Stop trading for the day if cumulative day PnL <= -threshold.
    Returns a mask of tradable timestamps (True if trading allowed).
    """
    df = pnl_series.to_frame("pnl").copy()
    df["date"] = df.index.tz_convert("UTC").date if hasattr(df.index, "tz") else df.index.date
    tradable = []
    for d, group in df.groupby("date"):
        cum = group["pnl"].cumsum()
        allow = cum > -(equity_start * (daily_loss_stop_pct / 100.0))
        tradable.append(allow)
    allow_mask = pd.concat(tradable).sort_index()
    return allow_mask

