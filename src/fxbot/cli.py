from __future__ import annotations

import argparse
import pathlib
import json
import pandas as pd

from .config import load_config
from .data.csv_loader import load_ohlcv_csv
from .strategies.momo_atr import generate_signals
from .backtest import run_backtest
from .report import save_report, export_report_to_csvs
from .optimize import grid_search
from .events import load_events_csv, build_blackout_mask
from .walkforward import walk_forward


def _slice_df(df: pd.DataFrame, start: str | None, end: str | None) -> pd.DataFrame:
    if start:
        df = df[df.index >= pd.to_datetime(start, utc=True)]
    if end:
        df = df[df.index <= pd.to_datetime(end, utc=True)]
    return df


def cmd_backtest(args: argparse.Namespace) -> None:
    cfg = load_config(args.config)
    df = load_ohlcv_csv(args.csv)
    df = _slice_df(df, getattr(args, "start", None), getattr(args, "end", None))
    params = cfg.strategy_params
    sig = generate_signals(
        df,
        ema_fast=int(params.get("ema_fast", 20)),
        ema_slow=int(params.get("ema_slow", 60)),
        atr_window=int(params.get("atr_window", 14)),
        vol_filter_min_atr_pct=float(params.get("vol_filter_min_atr_pct", 0.0)),
    )
    mask = None
    if getattr(args, "events", None):
        ev = load_events_csv(args.events)
        mask = build_blackout_mask(sig.index, ev, before_min=getattr(args, "blackout_before_min", 30), after_min=getattr(args, "blackout_after_min", 30))

    res = run_backtest(
        sig,
        start_cash=float(cfg.general.get("start_cash", 1_000_000)),
        atr_k_stop=float(params.get("atr_k_stop", 2.0)),
        slippage_pct=float(cfg.backtest_params.get("slippage_pct", 0.0)),
        fee_perc_roundturn=float(cfg.backtest_params.get("fee_perc_roundturn", 0.0)),
        per_trade_risk_pct=float(cfg.risk_params.get("per_trade_risk_pct", 0.25)),
        daily_loss_stop_pct=float(cfg.risk_params.get("daily_loss_stop_pct", 1.0)),
        entry_allowed_mask=mask,
    )

    out_dir = pathlib.Path(args.out).parent if args.out else cfg.report_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = pathlib.Path(args.out) if args.out else out_dir / f"report_{args.pair}.json"
    save_report(str(out_file), res)
    print(f"Saved report to: {out_file}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="fxbot")
    sub = p.add_subparsers(dest="command", required=True)

    # Backtest
    bt = sub.add_parser("backtest", help="Run backtest from CSV")
    bt.add_argument("--csv", required=True, help="Path to OHLCV CSV")
    bt.add_argument("--pair", required=True, help="Symbol/pair label for report filename")
    bt.add_argument("--config", default="config/config.yaml", help="Path to config.yaml")
    bt.add_argument("--out", default=None, help="Path to output report JSON")
    bt.add_argument("--start", default=None, help="YYYY-MM-DD or ISO start (optional)")
    bt.add_argument("--end", default=None, help="YYYY-MM-DD or ISO end (optional)")
    bt.add_argument("--events", default=None, help="Events CSV with 'timestamp' column (UTC)")
    bt.add_argument("--blackout-before-min", type=int, default=30, help="Minutes before event to block entries")
    bt.add_argument("--blackout-after-min", type=int, default=30, help="Minutes after event to block entries")
    bt.set_defaults(func=cmd_backtest)

    # Fetchers
    fy = sub.add_parser("fetch-yahoo", help="Fetch OHLCV from Yahoo and save CSV")
    fy.add_argument("--pair", required=True, help="FX pair (e.g., USDJPY, EURUSD, XAUUSD)")
    fy.add_argument("--interval", default="1h", help="1m/5m/15m/1h/1d")
    fy.add_argument("--period", default="2y", help="e.g., 7d, 60d, 1y, 2y; ignored if --start provided")
    fy.add_argument("--start", default=None, help="YYYY-MM-DD (optional)")
    fy.add_argument("--end", default=None, help="YYYY-MM-DD (optional)")
    fy.add_argument("--out", required=True, help="Output CSV path")

    def cmd_fetch_yahoo(args: argparse.Namespace) -> None:
        from .data.yahoo_loader import fetch_ohlcv_yahoo, save_df_to_csv as save_yahoo
        df = fetch_ohlcv_yahoo(args.pair, interval=args.interval, period=args.period, start=args.start, end=args.end)
        out = save_yahoo(df, args.out)
        print(f"Saved CSV: {out}")

    fy.set_defaults(func=cmd_fetch_yahoo)

    fa = sub.add_parser("fetch-alpha", help="Fetch OHLCV from Alpha Vantage (FX)")
    fa.add_argument("--pair", required=True, help="FX pair (e.g., USDJPY, EURUSD)")
    fa.add_argument("--interval", default="1h", help="1m/5m/15m/30m/60m or 1h")
    fa.add_argument("--out", required=True, help="Output CSV path")

    def cmd_fetch_alpha(args: argparse.Namespace) -> None:
        from .data.alpha_vantage_loader import fetch_ohlcv_alphavantage, save_df_to_csv as save_av
        df = fetch_ohlcv_alphavantage(args.pair, interval=args.interval)
        out = save_av(df, args.out)
        print(f"Saved CSV: {out}")

    fa.set_defaults(func=cmd_fetch_alpha)

    fs = sub.add_parser("fetch-stooq", help="Fetch OHLC from Stooq (daily)")
    fs.add_argument("--pair", required=True, help="FX pair (e.g., USDJPY, EURUSD)")
    fs.add_argument("--out", required=True, help="Output CSV path")

    def cmd_fetch_stooq(args: argparse.Namespace) -> None:
        from .data.stooq_loader import fetch_ohlcv_stooq, save_df_to_csv as save_stooq
        df = fetch_ohlcv_stooq(args.pair)
        out = save_stooq(df, args.out)
        print(f"Saved CSV: {out}")

    fs.set_defaults(func=cmd_fetch_stooq)

    fauto = sub.add_parser("fetch", help="Fetch with auto fallback: Yahoo -> Alpha -> Stooq")
    fauto.add_argument("--pair", required=True)
    fauto.add_argument("--interval", default="1h")
    fauto.add_argument("--out", required=True)

    def cmd_fetch_auto(args: argparse.Namespace) -> None:
        last_err = None
        try:
            from .data.yahoo_loader import fetch_ohlcv_yahoo, save_df_to_csv as save_yahoo
            df = fetch_ohlcv_yahoo(args.pair, interval=args.interval)
            out = save_yahoo(df, args.out)
            print(f"Saved CSV (Yahoo): {out}")
            return
        except Exception as e:
            last_err = e
            print(f"Yahoo fetch failed: {e}")
        try:
            from .data.alpha_vantage_loader import fetch_ohlcv_alphavantage, save_df_to_csv as save_av
            df = fetch_ohlcv_alphavantage(args.pair, interval=args.interval)
            out = save_av(df, args.out)
            print(f"Saved CSV (AlphaVantage): {out}")
            return
        except Exception as e:
            last_err = e
            print(f"AlphaVantage fetch failed: {e}")
        try:
            from .data.stooq_loader import fetch_ohlcv_stooq, save_df_to_csv as save_stooq
            df = fetch_ohlcv_stooq(args.pair)
            out = save_stooq(df, args.out)
            print(f"Saved CSV (Stooq daily): {out}")
            return
        except Exception as e:
            last_err = e
            print(f"Stooq fetch failed: {e}")
        raise SystemExit(f"All fetchers failed. Last error: {last_err}")

    fauto.set_defaults(func=cmd_fetch_auto)

    # Optimizer
    op = sub.add_parser("optimize", help="Grid search parameters on a CSV dataset")
    op.add_argument("--csv", required=True)
    op.add_argument("--pair", required=True)
    op.add_argument("--config", default="config/config.yaml")
    op.add_argument("--out", required=True, help="Output JSON for top results")
    op.add_argument("--ema-fast", default="10,20,30")
    op.add_argument("--ema-slow", default="50,80,120")
    op.add_argument("--atr-window", default="10,14,20")
    op.add_argument("--atr-k", default="1.5,2.0,2.5")
    op.add_argument("--atr-min-pct", default="0.0,0.01,0.02,0.03")
    op.add_argument("--ppyear", default=6048, type=int)
    op.add_argument("--start", default=None, help="YYYY-MM-DD or ISO start (optional)")
    op.add_argument("--end", default=None, help="YYYY-MM-DD or ISO end (optional)")

    def _parse_list(s: str, cast):
        return [cast(x) for x in s.split(",") if x.strip()]

    def cmd_optimize(args: argparse.Namespace) -> None:
        cfg = load_config(args.config)
        df = load_ohlcv_csv(args.csv)
        df = _slice_df(df, getattr(args, "start", None), getattr(args, "end", None))
        ef = _parse_list(args.__dict__["ema_fast"], int)
        es = _parse_list(args.__dict__["ema_slow"], int)
        aw = _parse_list(args.__dict__["atr_window"], int)
        ak = _parse_list(args.__dict__["atr_k"], float)
        av = _parse_list(args.__dict__["atr_min_pct"], float)
        res = grid_search(
            df,
            ema_fast_list=ef,
            ema_slow_list=es,
            atr_window_list=aw,
            atr_k_list=ak,
            vol_filter_min_atr_pct_list=av,
            start_cash=float(cfg.general.get("start_cash", 1_000_000)),
            slippage_pct=float(cfg.backtest_params.get("slippage_pct", 0.0)),
            fee_perc_roundturn=float(cfg.backtest_params.get("fee_perc_roundturn", 0.0)),
            per_trade_risk_pct=float(cfg.risk_params.get("per_trade_risk_pct", 0.25)),
            daily_loss_stop_pct=float(cfg.risk_params.get("daily_loss_stop_pct", 1.0)),
            periods_per_year=int(args.ppyear),
            max_dd_limit=None,
            top_n=10,
        )
        out_path = pathlib.Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
        print(f"Saved optimization results: {out_path}")

    op.set_defaults(func=cmd_optimize)

    # Backtest with best params
    bb = sub.add_parser("backtest-with-opt", help="Run backtest using top-1 params from optimize JSON")
    bb.add_argument("--csv", required=True)
    bb.add_argument("--pair", required=True)
    bb.add_argument("--config", default="config/config.yaml")
    bb.add_argument("--opt", required=True, help="Path to optimize results JSON")
    bb.add_argument("--out", required=True)
    bb.add_argument("--start", default=None)
    bb.add_argument("--end", default=None)

    def cmd_backtest_with_opt(args: argparse.Namespace) -> None:
        cfg = load_config(args.config)
        df = load_ohlcv_csv(args.csv)
        df = _slice_df(df, getattr(args, "start", None), getattr(args, "end", None))
        with open(args.opt, "r", encoding="utf-8") as f:
            arr = json.load(f)
        if not arr:
            raise SystemExit("opt results empty")
        top = arr[0]
        ef, es = int(top["ema_fast"]), int(top["ema_slow"]) 
        aw, ak = int(top["atr_window"]), float(top["atr_k"]) 
        av = float(top.get("vol_filter_min_atr_pct", 0.0))
        sig = generate_signals(df, ema_fast=ef, ema_slow=es, atr_window=aw, vol_filter_min_atr_pct=av)
        res = run_backtest(
            sig,
            start_cash=float(cfg.general.get("start_cash", 1_000_000)),
            atr_k_stop=ak,
            slippage_pct=float(cfg.backtest_params.get("slippage_pct", 0.0)),
            fee_perc_roundturn=float(cfg.backtest_params.get("fee_perc_roundturn", 0.0)),
            per_trade_risk_pct=float(cfg.risk_params.get("per_trade_risk_pct", 0.25)),
            daily_loss_stop_pct=float(cfg.risk_params.get("daily_loss_stop_pct", 1.0)),
        )
        out = pathlib.Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        save_report(str(out), res)
        print(f"Saved best-params report to: {out}")

    bb.set_defaults(func=cmd_backtest_with_opt)

    # Walk-Forward Validation
    wf = sub.add_parser("walkforward", help="Walk-forward validation with rolling optimization")
    wf.add_argument("--csv", required=True)
    wf.add_argument("--pair", required=True)
    wf.add_argument("--config", default="config/config.yaml")
    wf.add_argument("--out", required=True)
    wf.add_argument("--ema-fast", default="10,20,30")
    wf.add_argument("--ema-slow", default="50,80,120")
    wf.add_argument("--atr-window", default="10,14,20")
    wf.add_argument("--atr-k", default="1.5,2.0,2.5")
    wf.add_argument("--atr-min-pct", default="0.0,0.01,0.02")
    wf.add_argument("--train-bars", type=int, default=2000)
    wf.add_argument("--test-bars", type=int, default=500)
    wf.add_argument("--step-bars", type=int, default=0)
    wf.add_argument("--ppyear", default=6048, type=int)
    wf.add_argument("--events", default=None)
    wf.add_argument("--blackout-before-min", type=int, default=30)
    wf.add_argument("--blackout-after-min", type=int, default=30)
    wf.add_argument("--start", default=None)
    wf.add_argument("--end", default=None)

    def cmd_walkforward(args: argparse.Namespace) -> None:
        cfg = load_config(args.config)
        df = load_ohlcv_csv(args.csv)
        df = _slice_df(df, getattr(args, "start", None), getattr(args, "end", None))
        def _parse_list(s: str, cast):
            return [cast(x) for x in s.split(",") if x.strip()]
        ef = _parse_list(args.__dict__["ema_fast"], int)
        es = _parse_list(args.__dict__["ema_slow"], int)
        aw = _parse_list(args.__dict__["atr_window"], int)
        ak = _parse_list(args.__dict__["atr_k"], float)
        av = _parse_list(args.__dict__["atr_min_pct"], float)
        mask = None
        if args.events:
            ev = load_events_csv(args.events)
            mask = build_blackout_mask(df.index, ev, before_min=args.blackout_before_min, after_min=args.blackout_after_min)
        step = int(args.step_bars) if int(args.step_bars) > 0 else None
        result = walk_forward(
            df,
            train_bars=int(args.train_bars),
            test_bars=int(args.test_bars),
            step_bars=step,
            ema_fast_list=ef,
            ema_slow_list=es,
            atr_window_list=aw,
            atr_k_list=ak,
            vol_filter_min_atr_pct_list=av,
            start_cash=float(cfg.general.get("start_cash", 1_000_000)),
            slippage_pct=float(cfg.backtest_params.get("slippage_pct", 0.0)),
            fee_perc_roundturn=float(cfg.backtest_params.get("fee_perc_roundturn", 0.0)),
            per_trade_risk_pct=float(cfg.risk_params.get("per_trade_risk_pct", 0.25)),
            daily_loss_stop_pct=float(cfg.risk_params.get("daily_loss_stop_pct", 1.0)),
            periods_per_year=int(args.ppyear),
            entry_allowed_mask=mask,
        )
        out = pathlib.Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"Saved walk-forward results: {out}")

    wf.set_defaults(func=cmd_walkforward)

    # Report export to CSV
    rx = sub.add_parser("report-export", help="Export report JSON into CSV files")
    rx.add_argument("--in", dest="in_json", required=True, help="Path to report JSON produced by backtest")
    rx.add_argument("--out-dir", required=True, help="Directory to write CSVs (pnl.csv, trades.csv, summary.csv)")

    def cmd_report_export(args: argparse.Namespace) -> None:
        out = export_report_to_csvs(args.in_json, args.out_dir)
        print(json.dumps(out, ensure_ascii=False, indent=2))

    rx.set_defaults(func=cmd_report_export)

    return p


def main() -> None:
    p = build_parser()
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
