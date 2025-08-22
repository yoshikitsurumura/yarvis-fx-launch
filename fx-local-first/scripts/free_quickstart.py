#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from urllib.request import urlopen

# Reuse the offline engine (no external deps)
import importlib.util
from types import ModuleType


def _load_offline() -> ModuleType:
    here = Path(__file__).resolve().parent
    target = here / "offline_backtest.py"
    spec = importlib.util.spec_from_file_location("offline_backtest", str(target))
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load offline_backtest")
    import sys
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # ensure dataclasses see proper module
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


ob = _load_offline()


def fetch_stooq_daily(symbol: str, out_csv: Path) -> Path:
    s = symbol.lower()
    url = f"https://stooq.com/q/d/l/?s={s}&i=d"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(url, timeout=60) as resp, open(out_csv, "wb") as f:
        f.write(resp.read())
    return out_csv


def _build_blackout_set(rows, events_path: str | None, before_min: int, after_min: int):
    if not events_path:
        return None
    try:
        from datetime import datetime, timezone
        import csv as _csv
        ev = []
        with open(events_path, "r", encoding="utf-8") as f:
            r = _csv.DictReader(f)
            for row in r:
                low = {k.lower(): v for k, v in row.items()}
                ts = low.get("timestamp") or low.get("date")
                if not ts:
                    continue
                ev.append(datetime.fromisoformat(ts.replace("Z", "")).replace(tzinfo=timezone.utc))
        dis = set()
        for rr in rows:
            t = rr["timestamp"]
            for e in ev:
                dtm = (t - e).total_seconds() / 60.0
                if -before_min <= dtm <= after_min:
                    dis.add(t.isoformat())
        return dis
    except Exception:
        return None


def run_one(symbol: str, *, objective: str, min_trades: int, out_dir: Path, start: str | None, end: str | None, events: str | None, blackout_before: int, blackout_after: int) -> dict:
    csv_path = Path("data") / f"{symbol.upper()}_1d.csv"
    fetch_stooq_daily(symbol, csv_path)
    rows = ob.parse_csv(str(csv_path))
    rows = ob.filter_rows(rows, start, end)

    # Default grids matching offline_backtest
    ef = [10, 20, 30]
    es = [50, 80, 120]
    aw = [10, 14, 20]
    ak = [1.5, 2.0, 2.5]
    vf = [0.0, 0.02, 0.03]

    grid = ob.grid_search(
        rows,
        ema_fast_list=ef,
        ema_slow_list=es,
        atr_window_list=aw,
        atr_k_list=ak,
        vol_filter_list=vf,
        start_cash=1_000_000,
        slippage_pct=0.0001,
        fee_perc_roundturn=0.0002,
        per_trade_risk_pct=0.25,
        daily_loss_stop_pct=1.0,
    )
    filtered = [g for g in grid if g["metrics"].get("num_trades", 0) >= min_trades]
    cand = filtered if filtered else grid
    if not cand:
        return {"symbol": symbol.upper(), "error": "no params"}
    if objective == "sharpe":
        cand.sort(key=lambda x: x["metrics"].get("sharpe_approx", 0.0), reverse=True)
    else:
        cand.sort(key=lambda x: x["metrics"].get("total_return", 0.0), reverse=True)
    best = cand[0]

    # Re-run with best and export artifacts
    disallow = _build_blackout_set(rows, events, blackout_before, blackout_after)
    res = ob.run_backtest(
        rows,
        ema_fast=best["ema_fast"],
        ema_slow=best["ema_slow"],
        atr_window=best["atr_window"],
        vol_filter_min_atr_pct=best["vol_filter_min_atr_pct"],
        start_cash=1_000_000,
        atr_k_stop=best["atr_k"],
        slippage_pct=0.0001,
        fee_perc_roundturn=0.0002,
        per_trade_risk_pct=0.25,
        daily_loss_stop_pct=1.0,
        entry_disallow_set=disallow,
    )
    res["best_params"] = best

    pair_dir = out_dir / f"{symbol.upper()}_free"
    out_json = pair_dir / f"{symbol.upper()}_opt.json"
    out_csv_dir = pair_dir / "csv"
    ob.write_report(str(out_json), res)
    ob.export_csvs(str(out_json), str(out_csv_dir))

    met = ob.metrics_from_pnl(res.get("pnl_series", {}), res["start_cash"], res["end_cash"])
    return {
        "symbol": symbol.upper(),
        "best_params": best,
        "metrics": met,
        "json": str(out_json),
        "csv": str(out_csv_dir),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Free quickstart: fetch Stooq daily and optimize without external deps")
    ap.add_argument("--symbols", default="usdjpy,eurusd,xauusd")
    ap.add_argument("--objective", choices=["total_return", "sharpe"], default="sharpe")
    ap.add_argument("--min-trades", type=int, default=50)
    ap.add_argument("--out-dir", default="out/free_runs")
    ap.add_argument("--start", default=None, help="YYYY-MM-DD (optional)")
    ap.add_argument("--end", default=None, help="YYYY-MM-DD (optional)")
    ap.add_argument("--events", default=None, help="CSV with timestamp column (UTC)")
    ap.add_argument("--blackout-before-min", type=int, default=30)
    ap.add_argument("--blackout-after-min", type=int, default=30)
    args = ap.parse_args()

    syms = [s.strip() for s in args.symbols.split(",") if s.strip()]
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for s in syms:
        try:
            r = run_one(s, objective=args.objective, min_trades=args.min_trades, out_dir=out_dir, start=args.start, end=args.end, events=args.events, blackout_before=args.blackout_before_min, blackout_after=args.blackout_after_min)
        except Exception as e:
            r = {"symbol": s.upper(), "error": str(e)}
        results.append(r)

    # Write combined CSV summary
    summary_csv = out_dir / "summary_all.csv"
    with open(summary_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["symbol", "total_return", "sharpe_approx", "max_drawdown", "num_trades", "profit_factor", "json", "csv"])
        for r in results:
            m = r.get("metrics", {}) if isinstance(r, dict) else {}
            w.writerow([
                r.get("symbol"),
                m.get("total_return"),
                m.get("sharpe_approx"),
                m.get("max_drawdown"),
                m.get("num_trades"),
                m.get("profit_factor"),
                r.get("json"),
                r.get("csv"),
            ])

    # Write a simple Markdown report
    report_md = out_dir / "REPORT.md"
    def _fmt(x):
        if isinstance(x, (int,)):
            return str(x)
        try:
            return f"{float(x):.4f}"
        except Exception:
            return str(x)

    with open(report_md, "w", encoding="utf-8") as f:
        f.write("# Free Quickstart Results\n\n")
        if args.start or args.end:
            f.write(f"Period: {args.start or '-'} to {args.end or '-'}\n\n")
        if args.events:
            f.write(f"Blackout: ±{args.blackout_before_min}/{args.blackout_after_min} min around events in {args.events}\n\n")
        f.write("| Symbol | Total Return | Sharpe | Max DD | Trades | PF | JSON | CSV |\n")
        f.write("|---|---:|---:|---:|---:|---:|---|---|\n")
        # sort by objective
        def score(m):
            return (m.get("sharpe_approx", 0.0) if args.objective == "sharpe" else m.get("total_return", 0.0))
        ordered = sorted(results, key=lambda r: score(r.get("metrics", {})), reverse=True)
        for r in ordered:
            m = r.get("metrics", {}) if isinstance(r, dict) else {}
            f.write(f"| {r.get('symbol')} | {_fmt(m.get('total_return'))} | {_fmt(m.get('sharpe_approx'))} | {_fmt(m.get('max_drawdown'))} | {_fmt(m.get('num_trades'))} | {_fmt(m.get('profit_factor'))} | {r.get('json')} | {r.get('csv')} |\n")

    print(json.dumps({"out_dir": str(out_dir), "summary_csv": str(summary_csv), "report_md": str(report_md), "results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
