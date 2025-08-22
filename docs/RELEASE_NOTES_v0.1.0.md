# FX Local-First MVP v0.1.0 リリースノート

## 追加
- CLI: `optimize` / `walkforward` に `--start` / `--end` を追加（CSV読み込み後に期間スライスしてから実行）。
- Makefile（任意）: 補助ターゲットを追加。
  - `make fx-backtest-sample`: サンプルCSVでバックテスト（`out/report_sample.json`）。
  - `make fx-export-sample`: 直近レポートのCSV出力（`out/report_sample_csv/`）。
  - `make fx-help`: CLIヘルプを出力。

## 変更/Docs
- README: 最適化/Walk-Forwardの使用例に `--start` / `--end` を追記。

## 修正
- `src/fxbot/report.py`: `export_report_to_csvs` の末尾に残っていた重複コードを削除（到達不能/再定義を解消）。

## 互換性
- 破壊的変更はありません。既存のコマンドは従来どおり動作します。

## 既知事項
- オンライン取得系（Yahoo/Alpha/Stooq）は各サービスの規約・APIキーに依存します。ローカルCSVでの実行は影響ありません。

## バージョン
- パッケージ: `fxbot.__version__ = "0.1.0"`
