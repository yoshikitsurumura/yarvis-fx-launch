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

## クイックローンチ（GitHub Pages + Actions）
最短で公開するための手順です。考えることを最小化しています。

1) GitHubで空のリポジトリを作成（例: `https://github.com/<you>/<repo>.git`）
2) 初回のみ（このフォルダで）
```
git init
git add .
git commit -m "initial launch: lp/yarvis-fe/fxbot + actions"
git branch -M main
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```
3) GitHub Pages を有効化
- Repository → Settings → Pages → Build and deployment → Source: GitHub Actions を選択
4) Actions の結果確認（自動）
- deploy-pages: `…/index.html`, `…/lp/index.html`, `…/yarvis-fe/index.html` が公開
- CI: `fx_sanity` の Artifact `fx-sample` に JSON/CSV 一式
- e2e: Playwright テストが緑
5) A/Bリンクの共有（任意）
```
BASE=https://<username>.github.io/<repo>/ make pages-links
```
6) Alpha Vantage を使う場合のみ（任意）
- Repository → Settings → Secrets and variables → Actions → New repository secret → `ALPHAVANTAGE_API_KEY`

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
  --start 2023-01-01 \
  --end 2024-01-01 \
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
  --start 2021-01-01 \
  --end 2024-01-01 \
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

### 一括パイプライン（最短の実務フロー）
1) 依存導入・パス設定後、ワンコマンド実行
```
make fx-pipeline-quick
```
2) 出力
- `out/pipeline/<日時>/` 配下に以下を自動生成します。
  - `report.json`: 素のバックテスト結果
  - `opt.json`: グリッド最適化の上位結果
  - `report_best.json`: 最適パラメータでの再テスト結果
  - `csv/`: PnL/Trades/Summary のCSV一式
  - `walkforward.json`: Walk-Forward 検証結果
  - `SUMMARY.txt`: 次アクションの案内


## 依存ゼロで今すぐ試す（推奨ショートカット）
このリポジトリには、標準ライブラリのみで動く簡易バックテスト/最適化スクリプトを同梱しています。依存導入が難しい環境でも、公開データ（Stooqの日足）で検証できます。

## Web UI（視覚化）
- 目的: ブラウザでCSVを選択→バックテスト→エクイティ曲線と指標を表示。
- 依存追加: `Flask`（軽量Webフレームワーク）

手順（Windows PowerShell）
1) 準備
```
cd C:\Users\mayum\fx-local-first
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONPATH="src"
```
2) 起動
```
python scripts\webapp.py
```
3) ブラウザで表示
- `http://localhost:7860/` を開く
- 画面上部で `data\` 配下のCSVを選択し、「実行」をクリック
- 指標（総リターン、シャープ、最大DD 等）とエクイティ曲線を表示

補足
- 設定: `config\config.yaml` の戦略・バックテスト・リスク設定を使用します。
- ネットワーク不要: データはローカルCSVのみを参照します（Chart.jsはCDNを利用）。

### 便利機能（軽量・省メモリ対応）
- 設定保存/読込: 画面の「設定保存」ボタンで `out\webui_prefs.json` に保存、起動時に自動読込。
- 最大バー数（省メモリ）: 上限を指定すると読み込み後に末尾から制限し、内部の数値列はfloat32にダウンキャストします。
- トレードCSVダウンロード: 直近のバックテストのトレード一覧をCSVで保存。

### CSV列名の柔軟対応
- `timestamp/date/datetime/time` のいずれかを時刻として自動推測します。
- `volume` は任意（無い場合は0で補完）。
- Web UIの「列名マッピング」で実CSVの列名を指定可能（空なら自動推測）。

### AI連携（ローカルの推論関数を呼出し）
- Web UIの「AIシグナル」で `module:func` を指定すると、その関数が返すスコアをしきい値で長期シグナル化します。
- 例: 付属のサンプル
  - 関数: `scripts.ai_example:momentum_score`
  - しきい値: `0.5`
- 仕様: `func(df) -> pd.Series`（行インデックス揃え、0..1のスコア推奨）。

#### Geminiを使う（任意・オンライン）
- 目的: 直近バーの上昇確率をGeminiに推定させ、最終バーのスコアに反映（簡易）
- 手順:
  - `pip install google-generativeai`
  - PowerShell: `$env:GEMINI_API_KEY = "<あなたのキー>"`
  - Web UIのAI欄: `scripts.ai_gemini:gemini_score`
- 備考:
  - ネット接続/トークン費用が発生します。Local-Firstを優先する場合は未設定でOK（ローカル指標に自動フォールバック）。
  - 逐次バーごとの外部API呼び出しはコスト/レイテンシが高いため、検証や補助的な意思決定向けに限定して利用してください。

### コストガード（既定オフ）
- 既定ではオンラインAPIを使用しません。`FXBOT_ALLOW_ONLINE` が有効でない限り、Gemini等は無効化されローカルにフォールバックします。
- 有効化する（費用発生の可能性あり）場合のみ:
  - PowerShell: `$env:FXBOT_ALLOW_ONLINE = "1"`
  - さらに `$env:GEMINI_API_KEY` を設定し、`pip install google-generativeai`
- UIヘッダに「オンラインAPI: 許可/禁止」を表示します。

## E2Eテスト（Playwright）
- 目的: Web UIの起動と基本操作（CSV選択→実行）ができるかの自動確認。
- 手順（PowerShell、Web UIを別ターミナルで起動しておく）
```
# 1) サーバ起動（別ターミナル）
cd C:\Users\mayum\fx-local-first
. .\.venv\Scripts\Activate.ps1
python scripts\webapp.py

# 2) E2Eテスト実行
cd C:\Users\mayum\fx-local-first
. .\.venv\Scripts\Activate.ps1
pip install playwright
python -m playwright install chromium
python scripts\e2e_playwright.py
```
- 成果物: `out\e2e_screenshot.png` に画面キャプチャを保存。
- 備考: PlaywrightのブラウザDL時にネットワークが必要です。

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
 - 手順書（これだけ見ればOK）: `docs/STEP_BY_STEP_JA.md`

## LP / やーびす（収益導線の最小実装）
- `lp/`: 依存ゼロの静的LP（A/B切替付き）。
  - 表示: ブラウザで `lp/index.html` を開く
  - A/B: `?v=1` または `?v=2`（例: `lp/index.html?v=2&utm_source=lp&utm_medium=web&utm_campaign=launch`）
  - フォーム: `lp/config.example.js` を `lp/config.js` にコピーし、`window.LP_FORM_URL` をGoogleフォームURLに設定（UTM/variant自動付与）
- リンク生成: `make pages-links BASE=https://<pages-url>` で v1/v2/embed のURLを出力
- `yarvis-fe/`: やーびすの簡易MVP（一覧→詳細→実行[モック]/相談導線）。
  - 表示: ブラウザで `yarvis-fe/index.html` を開く（クエリはLPに引き継ぎ）
  - オプション: `?api=1` で `yarvis-fe/api/items.json` を読み込むモード

### GitHub Pages デプロイ（LPのみ）
- `main` へのpushで `.github/workflows/pages.yml` が `lp/` をサイトのルートとして自動公開します。
- 初回のみ、GitHubのリポジトリ設定で Pages を有効化してください（Source: GitHub Actions）。
- 公開後の配布例: `https://<pages-url>/?v=1` と `https://<pages-url>/?v=2`
- 公開後: `lp/robots.txt` の `Sitemap:` を公開URLに合わせて調整可

### ハンドオフ/実運用
- ハンドオフ要約: `docs/HANDOFF.md`
- あなたへの指示書: `docs/INSTRUCTIONS_FOR_YOU.md`
- Windowsクイックスタート: `docs/QUICKSTART_WINDOWS.md`
