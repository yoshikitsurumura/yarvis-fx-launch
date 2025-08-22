from __future__ import annotations

import itertools
from typing import Dict, Any, List

import pandas as pd

from .strategies.momo_atr import generate_signals
from .backtest import run_backtest
from .report import metrics_from_pnl


def grid_search(
    df: pd.DataFrame,
    *,
    ema_fast_list: List[int],
    ema_slow_list: List[int],
    atr_window_list: List[int],
    atr_k_list: List[float],
    vol_filter_min_atr_pct_list: List[float] | None = None,
    start_cash: float,
    slippage_pct: float,
    fee_perc_roundturn: float,
    per_trade_risk_pct: float,
    daily_loss_stop_pct: float,
    periods_per_year: int = 24 * 252,
    max_dd_limit: float | None = None,
    top_n: int = 10,
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    vol_list = vol_filter_min_atr_pct_list or [0.0]
    for ef, es, aw, ak, vf in itertools.product(
        ema_fast_list, ema_slow_list, atr_window_list, atr_k_list, vol_list
    ):
        # Enforce fast < slow to remove redundant/degenerate combos
        if ef >= es:
            continue
        sig = generate_signals(
            df,
            ema_fast=int(ef),
            ema_slow=int(es),
            atr_window=int(aw),
            vol_filter_min_atr_pct=float(vf),
        )
        res = run_backtest(
            sig,
            start_cash=start_cash,
            atr_k_stop=float(ak),
            slippage_pct=slippage_pct,
            fee_perc_roundturn=fee_perc_roundturn,
            per_trade_risk_pct=per_trade_risk_pct,
            daily_loss_stop_pct=daily_loss_stop_pct,
        )
        met = metrics_from_pnl(res["pnl_series"], start_cash, res["end_cash"], periods_per_year)
        # Filter by max drawdown if provided (limit as positive fraction, e.g., 0.2 for -20%)
        if max_dd_limit is not None:
            dd = float(met.get("max_drawdown", 0.0))
            if abs(dd) > max_dd_limit:
                continue
        results.append(
            {
                "ema_fast": int(ef),
                "ema_slow": int(es),
                "atr_window": int(aw),
                "atr_k": float(ak),
                "vol_filter_min_atr_pct": float(vf),
                **{k: float(v) if isinstance(v, (int, float)) else v for k, v in met.items()},
            }
        )

    # Sort by Sharpe approx desc, then total return desc
    def _key(x: Dict[str, Any]):
        return (
            float(x.get("sharpe_approx", 0.0)),
            float(x.get("total_return", 0.0)),
        )

    results.sort(key=_key, reverse=True)
    return results[: max(1, int(top_n))]
