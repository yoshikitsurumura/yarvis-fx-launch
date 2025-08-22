# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by Keep a Changelog. Versioning follows semantic versioning as guidance.

## [v0.1.0] - 2025-08-19

### Added
- CLI: `optimize` と `walkforward` に期間指定オプション `--start` / `--end` を追加。
  - CSV読み込み後に `_slice_df` で期間をスライスしてから最適化/Walk-Forwardを実行します。
- Makefile: 補助ターゲットを追加（任意利用）。
  - `make fx-backtest-sample`: サンプルCSVでバックテスト（`out/report_sample.json`）。
  - `make fx-export-sample`: 直近レポートのCSV出力（`out/report_sample_csv/`）。
  - `make fx-help`: CLIヘルプの出力。

### Changed / Docs
- README: 最適化・Walk-Forwardの使用例に `--start` / `--end` を追記。

### Fixed
- `src/fxbot/report.py`: `export_report_to_csvs` の処理末尾に残っていた重複コードを削除（到達不能・重複定義の解消）。

### Notes
- 破壊的変更はありません。既存のコマンドはそのまま動作します。
- オンライン取得系（Yahoo/Alpha/Stooq）は各サービスの規約・APIキーに依存します。ローカルCSVの動作は従来どおりです。

[v0.1.0]: https://example.com/releases/v0.1.0
