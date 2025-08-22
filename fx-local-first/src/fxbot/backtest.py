from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List

import numpy as np
import pandas as pd

from .risk import position_size_from_atr


@dataclass
class Trade:
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp | None
    entry: float
    exit: float | None
    size: float  # units
    atr_stop: float


def run_backtest(
    df_sig: pd.DataFrame,
    *,
    start_cash: float,
    atr_k_stop: float,
    slippage_pct: float = 0.0,
    fee_perc_roundturn: float = 0.0,
    per_trade_risk_pct: float = 0.25,
    daily_loss_stop_pct: float | None = None,
    entry_allowed_mask: pd.Series | None = None,
) -> Dict[str, Any]:
    """
    Long-only, flat/long switching. ATR stop. One position at a time.
    df_sig: DataFrame with columns [open, high, low, close, atr, signal]
    """
    df = df_sig.copy()
    cash = start_cash
    equity = start_cash
    position = 0.0
    entry_price = 0.0
    atr_stop = np.nan
    trades: List[Trade] = []
    pnl_series = pd.Series(0.0, index=df.index)
    # Track realized PnL per day for daily stop
    day_realized = {}

    for ts, row in df.iterrows():
        price = row["close"]
        sig = int(row.get("signal", 0))
        a = float(row.get("atr", np.nan))

        # Exit logic: if in position and signal drops or ATR stop hit
        if position > 0:
            stop_price = atr_stop
            # Stop-out on intrabar breach (approx by close below stop)
            exit_now = (sig == 0) or (price <= stop_price)
            if exit_now:
                # Apply slippage & fees
                px = price * (1.0 - slippage_pct)
                gross = (px - entry_price) * position
                fee = abs(px * position) * fee_perc_roundturn
                trade_pnl = gross - fee
                cash += trade_pnl
                equity = cash
                trades[-1].exit_time = ts
                trades[-1].exit = px
                position = 0.0
                entry_price = 0.0
                atr_stop = np.nan
                pnl_series.loc[ts] = trade_pnl
                # Accumulate daily realized PnL
                d = ts.tz_convert("UTC").date() if hasattr(ts, "tzinfo") and ts.tzinfo else ts.date()
                day_realized[d] = day_realized.get(d, 0.0) + float(trade_pnl)

        # Entry logic: if flat and signal is long
        if position == 0 and sig == 1 and np.isfinite(a) and a > 0:
            # Blackout window for entries
            if entry_allowed_mask is not None:
                allow = bool(entry_allowed_mask.get(ts, True))
                if not allow:
                    continue
            # Enforce daily loss stop: if reached threshold today, skip new entries
            if daily_loss_stop_pct is not None:
                d = ts.tz_convert("UTC").date() if hasattr(ts, "tzinfo") and ts.tzinfo else ts.date()
                realized_today = day_realized.get(d, 0.0)
                if realized_today <= -(start_cash * (daily_loss_stop_pct / 100.0)):
                    continue
            # size determined by ATR risk
            units = position_size_from_atr(
                entry_price=price,
                atr_value=a,
                atr_k_stop=atr_k_stop,
                equity=equity,
                per_trade_risk_pct=per_trade_risk_pct,
            )
            if units > 0:
                px = price * (1.0 + slippage_pct)
                fee = abs(px * units) * (fee_perc_roundturn / 2.0)
                # For FX, using units ~ notional JPY. Simplified cash handling.
                entry_price = px
                atr_stop = entry_price - atr_k_stop * a
                position = units
                trades.append(Trade(entry_time=ts, exit_time=None, entry=px, exit=None, size=units, atr_stop=atr_stop))
                cash -= fee
                equity = cash

    # Close any open position at last price
    if position > 0:
        last_ts = df.index[-1]
        price = df["close"].iloc[-1]
        px = price * (1.0 - slippage_pct)
        gross = (px - entry_price) * position
        fee = abs(px * position) * (fee_perc_roundturn / 2.0)
        trade_pnl = gross - fee
        cash += trade_pnl
        equity = cash
        trades[-1].exit_time = last_ts
        trades[-1].exit = px
        pnl_series.loc[last_ts] = trade_pnl

    result = {
        "start_cash": start_cash,
        "end_cash": cash,
        "trades": trades,
        "pnl_series": pnl_series,
    }
    return result
