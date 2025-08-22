# FX Local-First MVP (JP, Zero-Cost)

個人用・ローカル実行のFX解析/バックテスト基盤です。無料/ローカル優先、堅実運用（損失回避を重視）を目的に最小構成で作成しています。

- 実行: ローカルのみ（サーバー不要）。
- データ: 手元CSV読み込みを前提（無料ソースから各自取得）。
- 戦略: シンプルなモメンタム + ATRリスク管理の参考実装。
- 目的: 検証 → 紙トレ運用の安定性重視。実弾は自己責任で慎重に。

重要: 本ソフトは投資助言ではありません。成果や損失に関して一切の保証はありません。日本の関連法令・各サービス規約を遵守してください。

- マニュアル: `MANUAL.md`（無料フロー/Walk-Forward/フル機能の手順を網羅）

## セットアップ

1) Python 3.10+
2) 依存関係
```
pip install -r requirements.txt
```
3) 実行時のパス設定（未インストールでsrc配下を使うため）
```
export PYTHONPATH=src
```

## データ準備（CSV）
- 期待形式: 時系列のOHLCV。タイムゾーンはUTC推奨。
- 必須列: `timestamp, open, high, low, close, volume`
- 例: `data/USDJPY_1h.csv`

詳細は `data/README.md` を参照。

### Yahooから無料取得（推奨: 個人・検証用途）
- 依存: `yfinance`
- 例: USDJPYの1時間足を2年分取得してCSV保存
```
PYTHONPATH=src python -m fxbot.cli fetch-yahoo \
  --pair USDJPY \
  --interval 1h \
  --period 2y \
  --out data/USDJPY_1h.csv
```
- 注意: Yahooのデータ・規約・レート制限を遵守。商用利用は各自で条件を確認してください。

## 使い方

- バックテスト（CSVファイルを対象に実行）
```
PYTHONPATH=src python -m fxbot.cli backtest \
  --csv data/USDJPY_1h.csv \
  --pair USDJPY \
  --config config/config.yaml \
  --start 2023-01-01 \
  --end 2024-01-01 \
  --out out/report_USDJPY.json
```

- レポートのCSVエクスポート（PnL/Trades/Summary）
```
PYTHONPATH=src python -m fxbot.cli report-export \
  --in out/report_USDJPY.json \
  --out-dir out/report_USDJPY_csv
```
`out/report_USDJPY_csv/` に `pnl.csv`, `trades.csv`, `summary.csv` が保存されます。

### 自動フォールバック取得（Yahoo→AlphaVantage→Stooq）
```
PYTHONPATH=src python -m fxbot.cli fetch \
  --pair USDJPY \
  --interval 1h \
  --out data/USDJPY_1h.csv
```
注意: AlphaVantageを使う場合は `export ALPHAVANTAGE_API_KEY=...` を設定。

### かんたん最適化（グリッド探索）
```
PYTHONPATH=src python -m fxbot.cli optimize \
  --csv data/USDJPY_1h.csv \
  --pair USDJPY \
  --config config/config.yaml \
  --ema-fast 10,20,30 \
  --ema-slow 50,80,120 \
  --atr-window 10,14,20 \
  --atr-k 1.5,2.0,2.5 \
  --atr-min-pct 0.0,0.01,0.02,0.03 \
  --ppyear 6048 \
  --out out/opt_results.json
```
出力ファイルに上位パラメータと指標が保存されます。
`--atr-min-pct` は相対ATRの下限（例: 0.02=2%）で、低ボラ環境の除外に使います。

### 最適化結果で再テスト（トップ1）
```
PYTHONPATH=src python -m fxbot.cli backtest-with-opt \
  --csv data/USDJPY_1h.csv \
  --pair USDJPY \
  --config config/config.yaml \
  --opt out/opt_results.json \
  --out out/report_best.json
```

### Walk-Forward検証（過学習を避けるための分割検証）
```
PYTHONPATH=src python -m fxbot.cli walkforward \
  --csv data/USDJPY_1h.csv \
  --pair USDJPY \
  --config config/config.yaml \
  --ema-fast 10,20,30 \
  --ema-slow 50,80,120 \
  --atr-window 10,14,20 \
  --atr-k 1.5,2.0,2.5 \
  --atr-min-pct 0.0,0.01,0.02,0.03 \
  --train-bars 2000 \
  --test-bars 500 \
  --ppyear 6048 \
  --out out/walkforward.json
```
折り返しごとに学習→直近の検証を繰り返し、合算の損益指標を出力します。

### イベント・ブラックアウト（指標前後でエントリ回避）
- `events.csv` 形式（最低限）:
```
timestamp
2024-01-31 13:30:00
2024-02-14 13:30:00
```
- 実行例（前後30分を回避）:
```
PYTHONPATH=src python -m fxbot.cli backtest \
  --csv data/USDJPY_1h.csv \
  --pair USDJPY \
  --config config/config.yaml \
  --events data/events.csv \
  --blackout-before-min 30 \
  --blackout-after-min 30 \
  --out out/report_blackout.json
```

### 初心者向けクイックスタート（サンプルCSVで即実行）
1) 依存導入
```
pip install -r requirements.txt
export PYTHONPATH=src
```
2) サンプルデータでバックテスト
```
PYTHONPATH=src python -m fxbot.cli backtest \
  --csv data/sample_USDJPY_1h.csv \
  --pair USDJPY \
  --config config/config.yaml \
  --out out/report_sample.json
```
3) 結果確認
- `out/report_sample.json` に損益や指標（シャープ、最大DD）が出力されます。


- 設定: `config/config.yaml` に戦略・リスク・入出力設定を記載。

## 依存ゼロで今すぐ試す（推奨ショートカット）
このリポジトリには、標準ライブラリのみで動く簡易バックテスト/最適化スクリプトを同梱しています。依存導入が難しい環境でも、公開データ（Stooqの日足）で検証できます。

- USDJPY（日足）を取得→最適化（Sharpe最大化、最低50トレード）
```
curl -L -s 'https://stooq.com/q/d/l/?s=usdjpy&i=d' -o data/USDJPY_1d.csv
python3 scripts/offline_backtest.py \
  --csv data/USDJPY_1d.csv \
  --pair USDJPY \
  --out out/usdjpy_offline_opt.json \
  --out-dir out/usdjpy_offline_opt_csv \
  --optimize --objective sharpe --min-trades 50
```
- 他ペアの例（EURUSD/XAUUSD）
```
curl -L -s 'https://stooq.com/q/d/l/?s=eurusd&i=d' -o data/EURUSD_1d.csv
python3 scripts/offline_backtest.py --csv data/EURUSD_1d.csv --pair EURUSD --out out/eurusd_opt.json --out-dir out/eurusd_opt_csv --optimize --objective sharpe --min-trades 50

curl -L -s 'https://stooq.com/q/d/l/?s=xauusd&i=d' -o data/XAUUSD_1d.csv
python3 scripts/offline_backtest.py --csv data/XAUUSD_1d.csv --pair XAUUSD --out out/xauusd_opt.json --out-dir out/xauusd_opt_csv --optimize --objective sharpe --min-trades 50
```
- 出力: `out/...json` と `out/..._csv/summary.csv, trades.csv, pnl.csv`
- 注意: 簡易実装のため数値は概算です。厳密検証はpandas版CLIをご利用ください。

### 依存ゼロ Walk-Forward（期間・イベント対応）
```
python3 scripts/offline_backtest.py \
  --csv data/USDJPY_1d.csv --pair USDJPY \
  --out out/usdjpy_wf.json --out-dir out/usdjpy_wf_csv \
  --walkforward --objective sharpe --min-trades 20 \
  --train-bars 2000 --test-bars 500 --step-bars 0 \
  --start 1980-01-01 \
  --events data/events.csv --blackout-before-min 30 --blackout-after-min 30
```

## 戦略の概要
- EMAクロス（短期>長期でロング）
- ATRでボラフィルタ（低ボラ時のみ参入など調整可能）
- ATRストップ（初期ストップ = エントリ - k*ATR）
- 1トレードの口座リスク上限（例: 0.25%）
- 日次損失閾値で停止（例: 1%）

## 今後の拡張
- 無料データ取得の簡易コネクタ（Stooq, AlphaVantage Free 等）
- 経済指標カレンダーによるブラックアウト（手動CSVで対応可）
- Oanda Practice連携（任意・無料、ただしAPI規約順守）
- 簡易ダッシュボード（ローカルのみ）

## 免責
本リポジトリは教育/研究目的の参考実装です。投資判断はご自身で行い、法令・規約の遵守を徹底してください。

## ドキュメント
- 計画: `PLAN.md`
- 販売経路（デプロイ/動画/課金）: `docs/SALES_DEPLOY.md`
- 法務テンプレ: `docs/LEGAL/TERMS_TEMPLATE.md`, `docs/LEGAL/PRIVACY_TEMPLATE.md`
 - デモプレースホルダー: `docs/assets/demo.svg`（実際はmp4/gifを配置してリンクを差し替え）
