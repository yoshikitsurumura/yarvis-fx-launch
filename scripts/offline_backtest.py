#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from math import sqrt
from pathlib import Path
from typing import List, Dict, Any, Optional, Set


def parse_csv(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                # normalize keys to lower-case for robustness (e.g., Stooq: Date,Open,...)
                low = {k.lower(): v for k, v in row.items()}
                ts = low.get("timestamp") or low.get("date")
                if not ts:
                    continue
                # naive as UTC
                dt = datetime.fromisoformat(ts.replace("Z", "")).replace(tzinfo=timezone.utc)
                rows.append({
                    "timestamp": dt,
                    "open": float(low.get("open")),
                    "high": float(low.get("high")),
                    "low": float(low.get("low")),
                    "close": float(low.get("close")),
                    "volume": float(low.get("volume", 0.0) or 0.0),
                })
            except Exception:
                # skip bad row
                continue
    rows.sort(key=lambda x: x["timestamp"]) 
    return rows


def filter_rows(rows: List[Dict[str, Any]], start: Optional[str], end: Optional[str]) -> List[Dict[str, Any]]:
    if not rows:
        return rows
    sdt = None
    edt = None
    if start:
        sdt = datetime.fromisoformat(start).replace(tzinfo=timezone.utc)
    if end:
        edt = datetime.fromisoformat(end).replace(tzinfo=timezone.utc)
    out = []
    for r in rows:
        t = r["timestamp"]
        if sdt and t < sdt:
            continue
        if edt and t > edt:
            continue
        out.append(r)
    return out


def ema_series(values: List[float], span: int) -> List[Optional[float]]:
    if span <= 1:
        return [float(v) for v in values]
    alpha = 2.0 / (span + 1.0)
    out: List[Optional[float]] = []
    ema_val: Optional[float] = None
    for v in values:
        if ema_val is None:
            ema_val = float(v)
        else:
            ema_val = alpha * float(v) + (1.0 - alpha) * ema_val
        out.append(ema_val)
    return out


def atr_series(high: List[float], low: List[float], close: List[float], window: int) -> List[Optional[float]]:
    trs: List[float] = []
    prev_c: Optional[float] = None
    for h, l, c in zip(high, low, close):
        if prev_c is None:
            tr = float(h) - float(l)
        else:
            tr = max(float(h) - float(l), abs(float(h) - prev_c), abs(float(l) - prev_c))
        trs.append(tr)
        prev_c = float(c)
    return ema_series(trs, window)


@dataclass
class Trade:
    entry_time: datetime
    exit_time: Optional[datetime]
    entry: float
    exit: Optional[float]
    size: float
    atr_stop: float


def position_size_from_atr(entry_price: float, atr_value: float, atr_k_stop: float,
                           equity: float, per_trade_risk_pct: float) -> float:
    risk_jpy = equity * (per_trade_risk_pct / 100.0)
    stop_distance = atr_k_stop * atr_value
    if stop_distance <= 0:
        return 0.0
    units = risk_jpy / stop_distance
    return max(0.0, units)


def run_backtest(rows: List[Dict[str, Any]], *,
                 ema_fast: int, ema_slow: int, atr_window: int,
                 vol_filter_min_atr_pct: float,
                 start_cash: float, atr_k_stop: float,
                 slippage_pct: float, fee_perc_roundturn: float,
                 per_trade_risk_pct: float, daily_loss_stop_pct: Optional[float],
                 entry_disallow_set: Optional[Set[str]] = None) -> Dict[str, Any]:
    closes = [r["close"] for r in rows]
    highs = [r["high"] for r in rows]
    lows = [r["low"] for r in rows]
    ts = [r["timestamp"] for r in rows]

    ef = ema_series(closes, ema_fast)
    es = ema_series(closes, ema_slow)
    a = atr_series(highs, lows, closes, atr_window)

    signal: List[int] = []
    for i in range(len(rows)):
        mom = 1 if (ef[i] is not None and es[i] is not None and ef[i] > es[i]) else 0
        if vol_filter_min_atr_pct and a[i] is not None and closes[i] > 0:
            rel = a[i] / closes[i]
            vol_ok = rel >= vol_filter_min_atr_pct
            signal.append(1 if (mom == 1 and vol_ok) else 0)
        else:
            signal.append(mom)

    cash = start_cash
    equity = start_cash
    position = 0.0
    entry_price = 0.0
    atr_stop = float("nan")
    trades: List[Trade] = []
    pnl_series: Dict[str, float] = {}
    day_realized: Dict[str, float] = {}

    for i in range(len(rows)):
        price = closes[i]
        sig = signal[i]
        av = a[i] if a[i] is not None else 0.0
        t = ts[i]
        day_key = t.strftime("%Y-%m-%d")

        # Exit
        if position > 0:
            stop_price = atr_stop
            exit_now = (sig == 0) or (price <= stop_price)
            if exit_now:
                px = price * (1.0 - slippage_pct)
                gross = (px - entry_price) * position
                fee = abs(px * position) * fee_perc_roundturn
                trade_pnl = gross - fee
                cash += trade_pnl
                equity = cash
                tr = trades[-1]
                tr.exit_time = t
                tr.exit = px
                position = 0.0
                entry_price = 0.0
                atr_stop = float("nan")
                pnl_series[t.isoformat()] = trade_pnl
                day_realized[day_key] = day_realized.get(day_key, 0.0) + trade_pnl

        # Entry
        if position == 0 and sig == 1 and av > 0:
            if entry_disallow_set is not None and t.isoformat() in entry_disallow_set:
                continue
            if daily_loss_stop_pct is not None:
                realized_today = day_realized.get(day_key, 0.0)
                if realized_today <= -(start_cash * (daily_loss_stop_pct / 100.0)):
                    continue
            units = position_size_from_atr(
                entry_price=price,
                atr_value=av,
                atr_k_stop=atr_k_stop,
                equity=equity,
                per_trade_risk_pct=per_trade_risk_pct,
            )
            if units > 0:
                px = price * (1.0 + slippage_pct)
                fee = abs(px * units) * (fee_perc_roundturn / 2.0)
                entry_price = px
                atr_stop = entry_price - atr_k_stop * av
                position = units
                trades.append(Trade(entry_time=t, exit_time=None, entry=px, exit=None, size=units, atr_stop=atr_stop))
                cash -= fee
                equity = cash

    # Close at end
    if position > 0 and rows:
        price = closes[-1]
        t = ts[-1]
        px = price * (1.0 - slippage_pct)
        gross = (px - entry_price) * position
        fee = abs(px * position) * (fee_perc_roundturn / 2.0)
        trade_pnl = gross - fee
        cash += trade_pnl
        equity = cash
        tr = trades[-1]
        tr.exit_time = t
        tr.exit = px
        pnl_series[t.isoformat()] = trade_pnl

    return {
        "start_cash": start_cash,
        "end_cash": cash,
        "trades": trades,
        "pnl_series": pnl_series,
        "timestamps": [t.isoformat() for t in ts],
    }


def metrics_from_pnl(pnl_series: Dict[str, float], start_cash: float, end_cash: float,
                     periods_per_year: int = 24*252) -> Dict[str, Any]:
    # Sort by timestamp
    items = sorted(((k, v) for k, v in pnl_series.items()), key=lambda x: x[0])
    pnl = [v for _, v in items]
    equity_curve: List[float] = []
    eq = start_cash
    for x in pnl:
        eq += x
        equity_curve.append(eq)
    # returns
    rets: List[float] = []
    prev = start_cash
    for x in pnl:
        denom = prev if prev != 0 else 1.0
        rets.append(x / denom)
        prev += x
    # sharpe approx
    if not rets:
        sharpe = 0.0
    else:
        mean = sum(rets) / len(rets)
        var = sum((r - mean) ** 2 for r in rets) / len(rets)
        std = sqrt(var)
        sharpe = 0.0 if std == 0 else (mean / std) * sqrt(periods_per_year)
    # max drawdown
    max_dd = 0.0
    peak = start_cash
    eq = start_cash
    for x in pnl:
        eq += x
        if eq > peak:
            peak = eq
        dd = (eq - peak) / peak if peak != 0 else 0.0
        if dd < max_dd:
            max_dd = dd
    # trades stats
    trades_pnl = [x for x in pnl if abs(x) > 0]
    num_trades = len(trades_pnl)
    wins = [x for x in trades_pnl if x > 0]
    losses = [x for x in trades_pnl if x < 0]
    win_rate = (len(wins) / num_trades) if num_trades > 0 else 0.0
    avg_trade = (sum(trades_pnl) / num_trades) if num_trades > 0 else 0.0
    avg_win = (sum(wins) / len(wins)) if wins else 0.0
    avg_loss = (sum(losses) / len(losses)) if losses else 0.0
    gross_profit = sum(wins) if wins else 0.0
    gross_loss = sum(losses) if losses else 0.0
    profit_factor = (gross_profit / abs(gross_loss)) if gross_loss != 0 else (float('inf') if gross_profit > 0 else 0.0)
    total_return = (end_cash / start_cash) - 1.0 if start_cash > 0 else 0.0
    return {
        "total_return": float(total_return),
        "sharpe_approx": float(sharpe),
        "max_drawdown": float(max_dd),
        "num_trades": int(num_trades),
        "win_rate": float(win_rate),
        "avg_trade": float(avg_trade),
        "avg_win": float(avg_win),
        "avg_loss": float(avg_loss),
        "profit_factor": (None if profit_factor == float('inf') else float(profit_factor)),
    }


def write_report(out_json: str, res: Dict[str, Any]) -> None:
    trades = [asdict(t) for t in res["trades"]]
    summary = metrics_from_pnl(res["pnl_series"], res["start_cash"], res["end_cash"]) if res.get("pnl_series") else {}
    payload = {
        "start_cash": res["start_cash"],
        "end_cash": res["end_cash"],
        "summary": summary,
        "trades": trades,
        "pnl": res["pnl_series"],
    }
    Path(out_json).parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)


def export_csvs(in_json: str, out_dir: str) -> Dict[str, str]:
    with open(in_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    out: Dict[str, str] = {}
    # pnl.csv
    pnl = data.get("pnl", {})
    if isinstance(pnl, dict) and pnl:
        fp = Path(out_dir) / "pnl.csv"
        fp.parent.mkdir(parents=True, exist_ok=True)
        with open(fp, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["timestamp", "pnl"])
            for k, v in sorted(pnl.items(), key=lambda x: x[0]):
                w.writerow([k, v])
        out["pnl"] = str(fp)
    # trades.csv
    trades = data.get("trades", [])
    if isinstance(trades, list) and trades:
        fp = Path(out_dir) / "trades.csv"
        with open(fp, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            headers = ["entry_time", "exit_time", "entry", "exit", "size", "atr_stop"]
            w.writerow(headers)
            for t in trades:
                w.writerow([t.get("entry_time"), t.get("exit_time"), t.get("entry"), t.get("exit"), t.get("size"), t.get("atr_stop")])
        out["trades"] = str(fp)
    # summary.csv
    summary = data.get("summary", {})
    if isinstance(summary, dict) and summary:
        fp = Path(out_dir) / "summary.csv"
        with open(fp, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["metric", "value"])
            for k, v in summary.items():
                w.writerow([k, v])
        out["summary"] = str(fp)
    return out


def walk_forward(rows: List[Dict[str, Any]], *,
                 train_bars: int, test_bars: int, step_bars: Optional[int],
                 ema_fast_list: List[int], ema_slow_list: List[int],
                 atr_window_list: List[int], atr_k_list: List[float],
                 vol_filter_list: List[float], objective: str, min_trades: int,
                 start_cash: float, slippage_pct: float, fee_perc_roundturn: float,
                 per_trade_risk_pct: float, daily_loss_stop_pct: Optional[float],
                 entry_disallow_set: Optional[Set[str]] = None) -> Dict[str, Any]:
    n = len(rows)
    if n < train_bars + test_bars:
        return {"error": "not enough data"}
    step = step_bars if step_bars and step_bars > 0 else test_bars
    i0 = train_bars
    windows = []
    merged_pnl: Dict[str, float] = {}
    while i0 + test_bars <= n:
        tr_rows = rows[i0 - train_bars:i0]
        te_rows = rows[i0:i0 + test_bars]
        grid = grid_search(
            tr_rows,
            ema_fast_list=ema_fast_list,
            ema_slow_list=ema_slow_list,
            atr_window_list=atr_window_list,
            atr_k_list=atr_k_list,
            vol_filter_list=vol_filter_list,
            start_cash=start_cash,
            slippage_pct=slippage_pct,
            fee_perc_roundturn=fee_perc_roundturn,
            per_trade_risk_pct=per_trade_risk_pct,
            daily_loss_stop_pct=daily_loss_stop_pct,
        )
        cand = [g for g in grid if g["metrics"].get("num_trades", 0) >= min_trades]
        cand = cand if cand else grid
        if not cand:
            break
        if objective == "sharpe":
            cand.sort(key=lambda x: x["metrics"].get("sharpe_approx", 0.0), reverse=True)
        else:
            cand.sort(key=lambda x: x["metrics"].get("total_return", 0.0), reverse=True)
        best = cand[0]
        te_res = run_backtest(
            te_rows,
            ema_fast=best["ema_fast"], ema_slow=best["ema_slow"],
            atr_window=best["atr_window"], vol_filter_min_atr_pct=best["vol_filter_min_atr_pct"],
            start_cash=start_cash, atr_k_stop=best["atr_k"], slippage_pct=slippage_pct,
            fee_perc_roundturn=fee_perc_roundturn, per_trade_risk_pct=per_trade_risk_pct,
            daily_loss_stop_pct=daily_loss_stop_pct, entry_disallow_set=entry_disallow_set,
        )
        # merge pnl
        for k, v in te_res.get("pnl_series", {}).items():
            merged_pnl[k] = merged_pnl.get(k, 0.0) + float(v)
        winfo = {
            "train_start": tr_rows[0]["timestamp"].isoformat() if tr_rows else None,
            "train_end": tr_rows[-1]["timestamp"].isoformat() if tr_rows else None,
            "test_start": te_rows[0]["timestamp"].isoformat() if te_rows else None,
            "test_end": te_rows[-1]["timestamp"].isoformat() if te_rows else None,
            "best_params": best,
            "test_metrics": metrics_from_pnl(te_res.get("pnl_series", {}), te_res["start_cash"], te_res["end_cash"]),
        }
        windows.append(winfo)
        i0 += step
    overall = metrics_from_pnl(merged_pnl, start_cash, start_cash + sum(merged_pnl.values())) if merged_pnl else {}
    return {"windows": windows, "overall": overall, "pnl": merged_pnl}


def _parse_list(s: str, cast):
    return [cast(x) for x in s.split(",") if str(x).strip()]


def grid_search(rows: List[Dict[str, Any]], *,
                ema_fast_list: List[int], ema_slow_list: List[int], atr_window_list: List[int],
                atr_k_list: List[float], vol_filter_list: List[float],
                start_cash: float, slippage_pct: float, fee_perc_roundturn: float,
                per_trade_risk_pct: float, daily_loss_stop_pct: Optional[float]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for ef in ema_fast_list:
        for es in ema_slow_list:
            if ef >= es:
                # enforce fast < slow to avoid degenerate signals
                continue
            for aw in atr_window_list:
                for ak in atr_k_list:
                    for vf in vol_filter_list:
                        res = run_backtest(
                            rows,
                            ema_fast=ef,
                            ema_slow=es,
                            atr_window=aw,
                            vol_filter_min_atr_pct=vf,
                            start_cash=start_cash,
                            atr_k_stop=ak,
                            slippage_pct=slippage_pct,
                            fee_perc_roundturn=fee_perc_roundturn,
                            per_trade_risk_pct=per_trade_risk_pct,
                            daily_loss_stop_pct=daily_loss_stop_pct,
                        )
                        met = metrics_from_pnl(res.get("pnl_series", {}), res["start_cash"], res["end_cash"])
                        results.append({
                            "ema_fast": ef,
                            "ema_slow": es,
                            "atr_window": aw,
                            "atr_k": ak,
                            "vol_filter_min_atr_pct": vf,
                            "metrics": met,
                        })
    # sort by total_return desc, then sharpe
    results.sort(key=lambda x: (x["metrics"].get("total_return", 0.0), x["metrics"].get("sharpe_approx", 0.0)), reverse=True)
    return results


def main() -> None:
    ap = argparse.ArgumentParser(description="Offline backtest (no external deps)")
    ap.add_argument("--csv", required=True)
    ap.add_argument("--pair", required=True)
    ap.add_argument("--out", dest="out_json", required=True)
    ap.add_argument("--out-dir", dest="out_dir", required=True)
    ap.add_argument("--start", default=None, help="YYYY-MM-DD (optional)")
    ap.add_argument("--end", default=None, help="YYYY-MM-DD (optional)")
    # params (defaults aligned to config/config.yaml)
    ap.add_argument("--ema-fast", type=int, default=20)
    ap.add_argument("--ema-slow", type=int, default=60)
    ap.add_argument("--atr-window", type=int, default=14)
    ap.add_argument("--atr-k-stop", type=float, default=2.0)
    ap.add_argument("--vol-filter-min-atr-pct", type=float, default=0.03)
    ap.add_argument("--start-cash", type=float, default=1_000_000)
    ap.add_argument("--slippage-pct", type=float, default=0.0001)
    ap.add_argument("--fee-perc-roundturn", type=float, default=0.0002)
    ap.add_argument("--per-trade-risk-pct", type=float, default=0.25)
    ap.add_argument("--daily-loss-stop-pct", type=float, default=1.0)
    # Event blackout (optional)
    ap.add_argument("--events", default=None, help="CSV path with 'timestamp' column (UTC)")
    ap.add_argument("--blackout-before-min", type=int, default=30)
    ap.add_argument("--blackout-after-min", type=int, default=30)
    ap.add_argument("--optimize", action="store_true", help="Grid search for best params, then backtest with them")
    ap.add_argument("--ema-fast-list", default="10,20,30")
    ap.add_argument("--ema-slow-list", default="50,80,120")
    ap.add_argument("--atr-window-list", default="10,14,20")
    ap.add_argument("--atr-k-list", default="1.5,2.0,2.5")
    ap.add_argument("--vol-filter-list", default="0.0,0.02,0.03")
    ap.add_argument("--preset", choices=["balanced","conservative","aggressive"], default=None, help="Quick parameter grids preset")
    ap.add_argument("--objective", choices=["total_return","sharpe"], default="total_return")
    ap.add_argument("--min-trades", type=int, default=5, help="Prefer params with at least this many trades")
    # Walk-forward options
    ap.add_argument("--walkforward", action="store_true", help="Walk-forward validation using rolling optimization")
    ap.add_argument("--train-bars", type=int, default=2000)
    ap.add_argument("--test-bars", type=int, default=500)
    ap.add_argument("--step-bars", type=int, default=0)
    args = ap.parse_args()

    rows = parse_csv(args.csv)
    rows = filter_rows(rows, args.start, args.end)
    # Build blackout set if events provided
    disallow: Optional[Set[str]] = None
    if args.events:
        disallow = set()
        # load events
        ev_rows: List[datetime] = []
        try:
            with open(args.events, "r", encoding="utf-8") as f:
                r = csv.DictReader(f)
                for row in r:
                    low = {k.lower(): v for k, v in row.items()}
                    ts = low.get("timestamp") or low.get("date")
                    if not ts:
                        continue
                    ev_rows.append(datetime.fromisoformat(ts.replace("Z", "")).replace(tzinfo=timezone.utc))
        except Exception:
            ev_rows = []
        # build disallow set by windowing around events
        before = args.blackout_before_min
        after = args.blackout_after_min
        for rr in rows:
            t = rr["timestamp"]
            for e in ev_rows:
                if e and (e.replace(tzinfo=timezone.utc) if e.tzinfo is None else e):
                    dt = (t - e).total_seconds() / 60.0
                    if -before <= dt <= after:
                        disallow.add(t.isoformat())

    def _apply_preset():
        if not args.preset:
            return None
        if args.preset == "balanced":
            return (
                [10,20,30], [50,80,120], [10,14,20], [1.5,2.0,2.5], [0.0,0.02,0.03]
            )
        if args.preset == "conservative":
            return (
                [20,30], [100,120,150], [14,20], [2.0,2.5,3.0], [0.01,0.02,0.03]
            )
        if args.preset == "aggressive":
            return (
                [5,10], [30,50], [10,14], [1.2,1.5,2.0], [0.0,0.01]
            )
        return None

    if args.walkforward:
        ef = _parse_list(args.ema_fast_list, int)
        es = _parse_list(args.ema_slow_list, int)
        aw = _parse_list(args.atr_window_list, int)
        ak = _parse_list(args.atr_k_list, float)
        vf = _parse_list(args.vol_filter_list, float)
        preset = _apply_preset()
        if preset:
            ef, es, aw, ak, vf = preset
        wf = walk_forward(
            rows,
            train_bars=int(args.train_bars),
            test_bars=int(args.test_bars),
            step_bars=(int(args.step_bars) if int(args.step_bars) > 0 else None),
            ema_fast_list=ef,
            ema_slow_list=es,
            atr_window_list=aw,
            atr_k_list=ak,
            vol_filter_list=vf,
            objective=args.objective,
            min_trades=int(args.min_trades),
            start_cash=(args.start_cash if hasattr(args, 'start_cash') else 1_000_000),
            slippage_pct=args.slippage_pct,
            fee_perc_roundturn=args.fee_perc_roundturn,
            per_trade_risk_pct=args.per_trade_risk_pct,
            daily_loss_stop_pct=args.daily_loss_stop_pct,
            entry_disallow_set=disallow,
        )
        # Save WF JSON
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        with open(args.out_json, "w", encoding="utf-8") as f:
            json.dump(wf, f, ensure_ascii=False, indent=2)
        # Export overall PnL summary and windows csv
        out = export_csvs(args.out_json, args.out_dir)
        # windows.csv
        try:
            import itertools
            fpw = Path(args.out_dir) / "windows.csv"
            fpw.parent.mkdir(parents=True, exist_ok=True)
            with open(fpw, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["train_start","train_end","test_start","test_end","ema_fast","ema_slow","atr_window","atr_k","vol_filter","total_return","sharpe","max_dd","num_trades","profit_factor"])
                for win in wf.get("windows", []):
                    bp = win.get("best_params", {})
                    tm = win.get("test_metrics", {})
                    w.writerow([
                        win.get("train_start"), win.get("train_end"), win.get("test_start"), win.get("test_end"),
                        bp.get("ema_fast"), bp.get("ema_slow"), bp.get("atr_window"), bp.get("atr_k"), bp.get("vol_filter_min_atr_pct"),
                        tm.get("total_return"), tm.get("sharpe_approx"), tm.get("max_drawdown"), tm.get("num_trades"), tm.get("profit_factor"),
                    ])
            out["windows"] = str(fpw)
        except Exception:
            pass
        quick = {"csv_out": out, "overall": wf.get("overall", {}), "windows": len(wf.get("windows", []))}
        print(json.dumps(quick, ensure_ascii=False, indent=2))
        return
    elif args.optimize:
        ef = _parse_list(args.ema_fast_list, int)
        es = _parse_list(args.ema_slow_list, int)
        aw = _parse_list(args.atr_window_list, int)
        ak = _parse_list(args.atr_k_list, float)
        vf = _parse_list(args.vol_filter_list, float)
        preset = _apply_preset()
        if preset:
            ef, es, aw, ak, vf = preset
        grid = grid_search(
            rows,
            ema_fast_list=ef,
            ema_slow_list=es,
            atr_window_list=aw,
            atr_k_list=ak,
            vol_filter_list=vf,
            start_cash=args.start_cash,
            slippage_pct=args.slippage_pct,
            fee_perc_roundturn=args.fee_perc_roundturn,
            per_trade_risk_pct=args.per_trade_risk_pct,
            daily_loss_stop_pct=args.daily_loss_stop_pct,
        )
        # prefer parameter sets meeting min-trades
        filtered = [g for g in grid if g["metrics"].get("num_trades", 0) >= args.min_trades]
        cand = filtered if filtered else grid
        if args.objective == "sharpe":
            cand.sort(key=lambda x: x["metrics"].get("sharpe_approx", 0.0), reverse=True)
        else:
            cand.sort(key=lambda x: x["metrics"].get("total_return", 0.0), reverse=True)
        best = cand[0] if cand else None
        if best is None:
            print(json.dumps({"error": "no params found"}))
            return
        # re-run with best
        res = run_backtest(
            rows,
            ema_fast=best["ema_fast"],
            ema_slow=best["ema_slow"],
            atr_window=best["atr_window"],
            vol_filter_min_atr_pct=best["vol_filter_min_atr_pct"],
            start_cash=args.start_cash,
            atr_k_stop=best["atr_k"],
            slippage_pct=args.slippage_pct,
            fee_perc_roundturn=args.fee_perc_roundturn,
            per_trade_risk_pct=args.per_trade_risk_pct,
            daily_loss_stop_pct=args.daily_loss_stop_pct,
            entry_disallow_set=disallow,
        )
        res["best_params"] = best
        # also dump top-10
        res["top_params"] = grid[:10]
    else:
        res = run_backtest(
            rows,
            ema_fast=args.ema_fast,
            ema_slow=args.ema_slow,
            atr_window=args.atr_window,
            vol_filter_min_atr_pct=args.vol_filter_min_atr_pct,
            start_cash=args.start_cash,
            atr_k_stop=args.atr_k_stop,
            slippage_pct=args.slippage_pct,
            fee_perc_roundturn=args.fee_perc_roundturn,
            per_trade_risk_pct=args.per_trade_risk_pct,
            daily_loss_stop_pct=args.daily_loss_stop_pct,
            entry_disallow_set=disallow,
        )
    write_report(args.out_json, res)
    out = export_csvs(args.out_json, args.out_dir)
    # print concise summary for quick scan
    quick = {
        "csv_out": out,
        "summary": metrics_from_pnl(res.get("pnl_series", {}), res["start_cash"], res["end_cash"]),
    }
    if "best_params" in res:
        quick["best_params"] = res["best_params"]
    print(json.dumps(quick, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
