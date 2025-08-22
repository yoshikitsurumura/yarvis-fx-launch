#!/usr/bin/env python3
"""
FX 一括実行パイプライン（ローカル専用）

目的:
  最小操作で「バックテスト → 最適化 → ベスト再テスト → CSV出力 → Walk-Forward」を一気に実行。

使い方（例）:
  python scripts/fx_pipeline.py \
    --csv data/USDJPY_1h.csv --pair USDJPY --out-dir out/pipeline

引数省略時は以下の既定を使用:
  csv: data/USDJPY_1h.csv があればそれ、無ければ data/sample_USDJPY_1h.csv
  pair: USDJPY
  out-dir: out/pipeline

備考:
  - 内部で `python -m fxbot.cli` を順次呼び出します。
  - 事前に `pip install -r requirements.txt` を実行してください。
"""
from __future__ import annotations

import argparse
import os
import subprocess
from datetime import datetime
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


def sh(cmd: list[str]) -> None:
    env = os.environ.copy()
    # Ensure src is importable
    env["PYTHONPATH"] = str(SRC)
    print("$", " ".join(cmd))
    res = subprocess.run(cmd, env=env)
    if res.returncode != 0:
        raise SystemExit(res.returncode)


def guess_csv() -> str:
    p1 = ROOT / "data" / "USDJPY_1h.csv"
    p2 = ROOT / "data" / "sample_USDJPY_1h.csv"
    if p1.exists():
        return str(p1)
    if p2.exists():
        return str(p2)
    return str(p2)  # デフォルト（存在しない場合はエラーになります）


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--csv", default=guess_csv(), help="入力CSVパス")
    p.add_argument("--pair", default="USDJPY", help="通貨ペア名（例: USDJPY）")
    p.add_argument("--config", default=str(ROOT / "config" / "config.yaml"), help="設定ファイル")
    p.add_argument("--out-dir", default=str(ROOT / "out" / "pipeline"), help="出力ディレクトリの親（配下に日時別フォルダ作成）")
    p.add_argument("--start", default=None, help="開始日 (YYYY-MM-DD) 任意")
    p.add_argument("--end", default=None, help="終了日 (YYYY-MM-DD) 任意")
    p.add_argument("--ppyear", type=int, default=6048, help="年あたりポイント数（1h=24*252=6048 目安）")
    p.add_argument("--train-bars", type=int, default=2000, help="WFの学習本数")
    p.add_argument("--test-bars", type=int, default=500, help="WFの検証本数")
    p.add_argument("--atr-min", dest="atr_min", default="0.0,0.02,0.03", help="最適化時の atr-min-pct 候補（カンマ区切り）")
    a = p.parse_args()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_root = Path(a.out_dir)
    out_dir = out_root / ts
    out_dir.mkdir(parents=True, exist_ok=True)

    # Common flags
    base = [sys.executable, "-m", "fxbot.cli"]
    date_flags: list[str] = []
    if a.start:
        date_flags += ["--start", a.start]
    if a.end:
        date_flags += ["--end", a.end]

    # 1) Backtest (raw)
    report = out_dir / "report.json"
    cmd_bt = base + [
        "backtest",
        "--csv", a.csv,
        "--pair", a.pair,
        "--config", a.config,
        "--out", str(report),
    ] + date_flags
    sh(cmd_bt)

    # 2) Optimize (grid search)
    opt = out_dir / "opt.json"
    cmd_opt = base + [
        "optimize",
        "--csv", a.csv,
        "--pair", a.pair,
        "--config", a.config,
        "--ema-fast", "10,20,30",
        "--ema-slow", "50,80,120",
        "--atr-window", "10,14,20",
        "--atr-k", "1.5,2.0,2.5",
        "--atr-min-pct", a.atr_min,
        "--ppyear", str(a.ppyear),
        "--out", str(opt),
    ] + date_flags
    sh(cmd_opt)

    # 3) Backtest with best params
    report_best = out_dir / "report_best.json"
    cmd_bt_best = base + [
        "backtest-with-opt",
        "--csv", a.csv,
        "--pair", a.pair,
        "--config", a.config,
        "--opt", str(opt),
        "--out", str(report_best),
    ] + date_flags
    sh(cmd_bt_best)

    # 4) Export CSVs
    out_csv = out_dir / "csv"
    cmd_exp = base + [
        "report-export",
        "--in", str(report_best),
        "--out-dir", str(out_csv),
    ]
    sh(cmd_exp)

    # 5) Walk-Forward
    wf = out_dir / "walkforward.json"
    cmd_wf = base + [
        "walkforward",
        "--csv", a.csv,
        "--pair", a.pair,
        "--config", a.config,
        "--ema-fast", "10,20,30",
        "--ema-slow", "50,80,120",
        "--atr-window", "10,14,20",
        "--atr-k", "1.5,2.0,2.5",
        "--atr-min-pct", a.atr_min,
        "--train-bars", str(a.train_bars),
        "--test-bars", str(a.test_bars),
        "--ppyear", str(a.ppyear),
        "--out", str(wf),
    ] + date_flags
    sh(cmd_wf)

    # Summary
    summary = out_dir / "SUMMARY.txt"
    lines = [
        "# FX Pipeline Summary\n",
        f"csv: {a.csv}",
        f"pair: {a.pair}",
        f"period: {a.start or '-'} ~ {a.end or '-'}",
        "",
        f"report (raw): {report}",
        f"opt results:  {opt}",
        f"report (best): {report_best}",
        f"exported csv: {out_csv}",
        f"walk-forward: {wf}",
        "",
        "Next: 生成された CSV と JSON を確認し、安定パラメータを config.yaml に反映してください。",
    ]
    summary.write_text("\n".join(lines), encoding="utf-8")
    print("\n=== Done ===")
    print(f"Output dir: {out_dir}")
    print("Open SUMMARY.txt for next steps.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)

