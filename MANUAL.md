# FX Local-First MVP マニュアル（無料フロー対応）

本マニュアルは、無料データと標準ライブラリのみで「すぐ動く」検証フローと、依存ありのフル機能フローを簡潔にまとめたものです。

重要: 本ソフトは投資助言ではありません。成果や損失に関して一切の保証はありません。法令・各サービス規約を遵守してください。

## 1. 構成
- コア実装（依存あり: pandas 等）: `src/fxbot/`（CLI: `fxbot.cli`）
- 依存ゼロの簡易ツール:
  - `scripts/offline_backtest.py`: バックテスト/最適化/Walk-Forward（CSV→JSON/CSV出力）
  - `scripts/free_quickstart.py`: ペアの一括取得（Stooq）+最適化+集計（ワンコマンド）

## 2. 無料・依存ゼロフロー（推奨ショートカット）
### 2.1 まとめ実行（複数ペア）
```
python3 scripts/free_quickstart.py \
  --symbols usdjpy,eurusd,xauusd \
  --objective sharpe \
  --min-trades 50 \
  --start 2015-01-01
```
- 出力: `out/free_runs/summary_all.csv`, `out/free_runs/REPORT.md`
- 各ペア成果: `out/free_runs/<PAIR>_free/<PAIR>_opt.json` と `csv/{summary,trades,pnl}.csv`

### 2.2 単独ペアの最適化
```
curl -L -s 'https://stooq.com/q/d/l/?s=usdjpy&i=d' -o data/USDJPY_1d.csv
python3 scripts/offline_backtest.py \
  --csv data/USDJPY_1d.csv --pair USDJPY \
  --out out/usdjpy_opt.json --out-dir out/usdjpy_opt_csv \
  --optimize --objective sharpe --min-trades 50 \
  --start 2015-01-01
```

### 2.3 Walk-Forward 検証（依存ゼロ版）
```
python3 scripts/offline_backtest.py \
  --csv data/USDJPY_1d.csv --pair USDJPY \
  --out out/usdjpy_wf.json --out-dir out/usdjpy_wf_csv \
  --walkforward --objective sharpe --min-trades 20 \
  --train-bars 2000 --test-bars 500 --step-bars 0 \
  --start 1980-01-01
```
- 出力概要（例）: overall（合成PnLの指標）, windows（分割数）, `pnl.csv`

ヒント:
- `--objective total_return` で収益重視に切替。
- `--min-trades` で取引数下限を引き上げ、過剰最適化を抑制。
- 期間は `--start/--end` で指定（ISO日付）。

### 2.4 プリセットの利用（候補帯の一括切替）
最適化・Walk-Forward両方で `--preset` を使うと、探索グリッドを一括で切り替えできます。

```
# バランス（デフォルト相当）
--preset balanced

# 保守的（長期EMA/大きめATRストップ/高めボラ閾値）
--preset conservative

# 攻め（短期EMA/小さめATRストップ/低ボラ許容）
--preset aggressive
```

### 2.5 イベント・ブラックアウト
`--events` でUTCのイベント時刻をCSV指定し、前後分をエントリ禁止にできます。

```
# events.csv 例
timestamp
2024-01-31 13:30:00
2024-02-14 13:30:00

# 実行例（±30分回避）
--events data/events.csv --blackout-before-min 30 --blackout-after-min 30
```

## 3. 依存ありのフル機能（厳密検証）
### 3.1 セットアップ
```
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=src
```

### 3.2 代表コマンド
- バックテスト:
```
python -m fxbot.cli backtest --csv data/USDJPY_1h.csv --pair USDJPY --config config/config.yaml --out out/report.json
```
- 最適化（グリッド）:
```
python -m fxbot.cli optimize --csv data/USDJPY_1h.csv --pair USDJPY --config config/config.yaml --out out/opt.json
```
- Walk-Forward:
```
python -m fxbot.cli walkforward --csv data/USDJPY_1h.csv --pair USDJPY --config config/config.yaml --out out/wf.json
```
- レポートCSV出力:
```
python -m fxbot.cli report-export --in out/report.json --out-dir out/report_csv
```

## 4. データ仕様（CSV）
- 必須列: `timestamp, open, high, low, close, volume`
- タイムゾーン: UTC推奨。
- Stooq日足の場合は `Date,Open,High,Low,Close` 列に自動対応。

## 5. 推奨ワークフロー
1) 無料フローで素早く比較（free_quickstart）
2) 有望ペアを選定 → 依存ゼロWalk-Forwardで過学習チェック
3) 本命ペアをpandas版で厳密検証（必要に応じてイベントブラックアウトも）

クイックレシピ:
- 直近10年をSharpe最大化で比較: `scripts/free_quickstart.py --start 2015-01-01 --objective sharpe`
- 直近5年を収益最大化で比較: `scripts/free_quickstart.py --start 2020-01-01 --objective total_return`
- 有望ペアをWFで再検証: `scripts/offline_backtest.py --walkforward --train-bars 2000 --test-bars 500`

## 6. トラブルシュート
- 取引数が極端に少ない: `--min-trades` を上げる or 期間を延長
- 指標が高すぎる/不自然: 窓数・取引数のしきい値を調整し、Walk-Forwardで再検証
- 依存が入らない: まず依存ゼロフローで検証→別環境でpandas版に移行

## 7. 免責と遵守
- 本実装は教育・研究目的の参考。投資判断は自己責任。
- 各データソースの利用規約・レート制限を順守。

以上。
