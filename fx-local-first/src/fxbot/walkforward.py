from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Tuple

import pandas as pd

from .strategies.momo_atr import generate_signals
from .backtest import run_backtest
from .report import metrics_from_pnl
from .optimize import grid_search


@dataclass
class FoldResult:
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    params: Dict[str, Any]
    metrics: Dict[str, Any]


def walk_forward(
    df: pd.DataFrame,
    *,
    train_bars: int,
    test_bars: int,
    step_bars: int | None,
    ema_fast_list: List[int],
    ema_slow_list: List[int],
    atr_window_list: List[int],
    atr_k_list: List[float],
    vol_filter_min_atr_pct_list: List[float] | None,
    start_cash: float,
    slippage_pct: float,
    fee_perc_roundturn: float,
    per_trade_risk_pct: float,
    daily_loss_stop_pct: float,
    periods_per_year: int,
    entry_allowed_mask: pd.Series | None = None,
) -> Dict[str, Any]:
    n = len(df)
    if n < train_bars + test_bars:
        raise ValueError("Not enough data for one fold")
    step = step_bars or test_bars
    i = 0
    folds: List[FoldResult] = []
    combined_pnl_parts: List[pd.Series] = []
    cash = start_cash

    while i + train_bars + test_bars <= n:
        trn = df.iloc[i : i + train_bars]
        tst = df.iloc[i + train_bars : i + train_bars + test_bars]

        top = grid_search(
            trn,
            ema_fast_list=ema_fast_list,
            ema_slow_list=ema_slow_list,
            atr_window_list=atr_window_list,
            atr_k_list=atr_k_list,
            vol_filter_min_atr_pct_list=vol_filter_min_atr_pct_list,
            start_cash=cash,  # use current cash as starting capital reference
            slippage_pct=slippage_pct,
            fee_perc_roundturn=fee_perc_roundturn,
            per_trade_risk_pct=per_trade_risk_pct,
            daily_loss_stop_pct=daily_loss_stop_pct,
            periods_per_year=periods_per_year,
            max_dd_limit=None,
            top_n=1,
        )
        if not top:
            break
        best = top[0]
        ef, es = int(best["ema_fast"]), int(best["ema_slow"]) 
        aw, ak = int(best["atr_window"]), float(best["atr_k"]) 

        vmin = float(best.get("vol_filter_min_atr_pct", 0.0))
        sig_tst = generate_signals(tst, ema_fast=ef, ema_slow=es, atr_window=aw, vol_filter_min_atr_pct=vmin)
        mask = None
        if entry_allowed_mask is not None:
            # Align blackout mask to test index
            mask = entry_allowed_mask.reindex(sig_tst.index).fillna(True)
        res = run_backtest(
            sig_tst,
            start_cash=cash,
            atr_k_stop=ak,
            slippage_pct=slippage_pct,
            fee_perc_roundturn=fee_perc_roundturn,
            per_trade_risk_pct=per_trade_risk_pct,
            daily_loss_stop_pct=daily_loss_stop_pct,
            entry_allowed_mask=mask,
        )
        met = metrics_from_pnl(res["pnl_series"], cash, res["end_cash"], periods_per_year)
        folds.append(
            FoldResult(
                train_start=str(trn.index[0]),
                train_end=str(trn.index[-1]),
                test_start=str(tst.index[0]),
                test_end=str(tst.index[-1]),
                params={"ema_fast": ef, "ema_slow": es, "atr_window": aw, "atr_k": ak, "vol_filter_min_atr_pct": vmin},
                metrics=met,
            )
        )
        combined_pnl_parts.append(res["pnl_series"])
        cash = float(res["end_cash"])  # roll forward
        i += step

    combined_pnl = pd.concat(combined_pnl_parts).sort_index() if combined_pnl_parts else pd.Series(dtype=float)
    summary = metrics_from_pnl(combined_pnl, start_cash, cash, periods_per_year) if len(combined_pnl) else {}
    return {
        "start_cash": start_cash,
        "end_cash": cash,
        "summary": summary,
        "folds": [
            {
                "train_start": f.train_start,
                "train_end": f.train_end,
                "test_start": f.test_start,
                "test_end": f.test_end,
                "params": f.params,
                "metrics": f.metrics,
            }
            for f in folds
        ],
    }
