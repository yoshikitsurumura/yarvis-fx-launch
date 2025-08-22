from __future__ import annotations

import json
from dataclasses import asdict
import pathlib
from typing import Dict, Any

import numpy as np
import pandas as pd


def metrics_from_pnl(pnl: pd.Series, start_cash: float, end_cash: float, periods_per_year: int | None = None) -> Dict[str, Any]:
    pnl = pnl.fillna(0.0)
    equity_curve = start_cash + pnl.cumsum()
    ret = pnl / equity_curve.shift(1).replace(0, np.nan)
    ret = ret.fillna(0.0)
    ann_factor = periods_per_year if periods_per_year else 24 * 252
    sharpe = 0.0 if ret.std(ddof=0) == 0 else (ret.mean() / ret.std(ddof=0)) * np.sqrt(ann_factor)
    peak = equity_curve.cummax()
    dd = (equity_curve - peak) / peak
    max_dd = dd.min() if len(dd) else 0.0
    total_return = (end_cash / start_cash) - 1.0 if start_cash > 0 else 0.0

    # Trade-level stats inferred from pnl series (each nonzero = a closed trade)
    trades_pnl = pnl[pnl != 0.0]
    num_trades = int(trades_pnl.shape[0])
    wins = trades_pnl[trades_pnl > 0]
    losses = trades_pnl[trades_pnl < 0]
    win_rate = float(len(wins)) / num_trades if num_trades > 0 else 0.0
    avg_trade = float(trades_pnl.mean()) if num_trades > 0 else 0.0
    avg_win = float(wins.mean()) if len(wins) > 0 else 0.0
    avg_loss = float(losses.mean()) if len(losses) > 0 else 0.0
    gross_profit = float(wins.sum()) if len(wins) > 0 else 0.0
    gross_loss = float(losses.sum()) if len(losses) > 0 else 0.0
    profit_factor = (gross_profit / abs(gross_loss)) if gross_loss != 0 else (np.inf if gross_profit > 0 else 0.0)

    return {
        "total_return": float(total_return),
        "sharpe_approx": float(sharpe),
        "max_drawdown": float(max_dd),
        "num_trades": num_trades,
        "win_rate": float(win_rate),
        "avg_trade": float(avg_trade),
        "avg_win": float(avg_win),
        "avg_loss": float(avg_loss),
        "profit_factor": float(profit_factor) if np.isfinite(profit_factor) else None,
    }


def save_report(path: str, result: Dict[str, Any]) -> None:
    trades = result.get("trades", [])
    trades_ser = [asdict(t) for t in trades]
    pnl = result.get("pnl_series")
    pnl_ser = pnl.astype(float).to_dict() if isinstance(pnl, pd.Series) else {}
    summary = metrics_from_pnl(pnl, result["start_cash"], result["end_cash"]) if isinstance(pnl, pd.Series) else {}
    payload = {
        "start_cash": result.get("start_cash"),
        "end_cash": result.get("end_cash"),
        "summary": summary,
        "trades": trades_ser,
        "pnl": pnl_ser,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)


def export_report_to_csvs(path: str, out_dir: str) -> Dict[str, str]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    out = {}
    # PnL CSV
    pnl = data.get("pnl", {})
    if isinstance(pnl, dict) and pnl:
        df_pnl = pd.DataFrame({"timestamp": list(pnl.keys()), "pnl": list(pnl.values())})
        df_pnl["timestamp"] = pd.to_datetime(df_pnl["timestamp"], utc=True)
        df_pnl = df_pnl.sort_values("timestamp")
        fp = pathlib.Path(out_dir) / "pnl.csv"
        fp.parent.mkdir(parents=True, exist_ok=True)
        df_pnl.to_csv(fp, index=False)
        out["pnl"] = str(fp)
    # Trades CSV
    trades = data.get("trades", [])
    if isinstance(trades, list) and trades:
        df_tr = pd.DataFrame(trades)
        fp = pathlib.Path(out_dir) / "trades.csv"
        fp.parent.mkdir(parents=True, exist_ok=True)
        df_tr.to_csv(fp, index=False)
        out["trades"] = str(fp)
    # Summary CSV
    summary = data.get("summary", {})
    if isinstance(summary, dict) and summary:
        df_sm = pd.DataFrame(list(summary.items()), columns=["metric", "value"])
        fp = pathlib.Path(out_dir) / "summary.csv"
        fp.parent.mkdir(parents=True, exist_ok=True)
        df_sm.to_csv(fp, index=False)
        out["summary"] = str(fp)
    return out
    trades = result.get("trades", [])
    trades_ser = [asdict(t) for t in trades]
    pnl = result.get("pnl_series")
    pnl_ser = pnl.astype(float).to_dict() if isinstance(pnl, pd.Series) else {}
    summary = metrics_from_pnl(pnl, result["start_cash"], result["end_cash"]) if isinstance(pnl, pd.Series) else {}
    payload = {
        "start_cash": result.get("start_cash"),
        "end_cash": result.get("end_cash"),
        "summary": summary,
        "trades": trades_ser,
        "pnl": pnl_ser,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
