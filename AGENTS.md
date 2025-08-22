# FX Local-First MVP — Agent Guidelines

本ドキュメントは、このリポジトリで作業するAIアシスタント（および関係者）向けのガイドラインです。目的は「安全・簡潔・丁寧・再現可能」な進め方を統一することです。

## 目的と範囲
- 目的: ローカル優先のFXバックテスト/最適化ツールの開発・保守。
- 範囲: `src/fxbot` 一式、`config/`・`data/`・`README.md` など付随ドキュメント。
- 非目的: 投資助言。法令・規約違反につながる行為。

## コミュニケーション方針（日本語・丁寧）
- 口調: 丁寧語で簡潔に。断定を避け、具体的な次アクションを提示。
- 進捗共有: 1–2文で「何をした/何をするか」を明示。
- 書式:
  - 短い見出し（必要なときのみ）。
  - 箇条書きは 4–6 項目を上限の目安に整理。
  - コマンド・ファイルパス・識別子はバッククォートで囲む（例: `python -m fxbot.cli backtest`).
- 依頼: 実行確認や環境変数設定など、人に依頼する内容は明確に列挙して短く。

## ツール実行の原則（Codex CLI 前提）
- 実行前プレアンブル: 1–2文で「これから何をするか」を通知。
- 計画（Plan）の更新: 複数ステップの場合は `update_plan` を活用。完了/進行中を正しく管理。
- 変更は最小差分: 不要な改名や広範なリファクタは避ける。関連外の修正は行わない。
- 権限/サンドボックス: ネットワークや外部書き込みが必要な場合は、その理由を1文で示し、承認を得る。

## コーディング指針
- スタイル: 既存コードのスタイルに合わせる。過度な抽象化は避ける。
- 命名: 意図が伝わる実用的な名前。1文字変数は避ける。
- ドキュメント: CLIや設定に影響する変更では `README.md` を更新。
- 互換性: 破壊的変更は避ける。やむを得ない場合は明示し、移行手順を簡潔に記載。
- 依存: 新規依存の追加は慎重に。可能な限り既存依存で実装。

## テスト/検証方針
- 局所検証を優先: 変更箇所に近い最小の実行/確認を行い、問題箇所を早期発見。
- 既存の実行パスで検証: 例) `backtest` → JSON生成 → `report-export` でCSV出力。
- 失敗時はメッセージに根拠を示し、代替案を提案。

## データと法令順守
- データ取得は各ソースの規約・レート制限を順守。
- 無料APIキー（Alpha Vantageなど）はユーザー環境変数にて管理し、コードへ直書きしない。
- 個人情報・秘密情報は扱わない。必要に応じた最小限のログに留める。

## 変更の型（例）
- 仕様追加: CLIフラグ・出力の追加。`README.md` に追記。
- バグ修正: 原因を特定し、最小差分で修正。影響範囲を記述。
- ドキュメント: 実行手順・例・注意点を簡潔に更新。

## 出力の品質基準
- 簡潔: 余分な前提や蛇足は避ける。
- 再現性: 同じ手順で同じ結果が得られるよう記述。
- 丁寧: 不確実な点は「推測」であることを明言。代替案を添える。

## よく使うコマンド例
- バックテスト:
  - `PYTHONPATH=src python -m fxbot.cli backtest --csv data/USDJPY_1h.csv --pair USDJPY --config config/config.yaml --out out/report.json`
- 最適化（ボラ下限含む）:
  - `PYTHONPATH=src python -m fxbot.cli optimize --csv data/USDJPY_1h.csv --pair USDJPY --config config/config.yaml --ema-fast 10,20,30 --ema-slow 50,80,120 --atr-window 10,14,20 --atr-k 1.5,2.0,2.5 --atr-min-pct 0.0,0.02,0.03 --out out/opt.json`
- Walk-Forward:
  - `PYTHONPATH=src python -m fxbot.cli walkforward --csv data/USDJPY_1h.csv --pair USDJPY --config config/config.yaml --train-bars 2000 --test-bars 500 --atr-min-pct 0.0,0.02 --out out/wf.json`
- レポートCSV出力:
  - `PYTHONPATH=src python -m fxbot.cli report-export --in out/report.json --out-dir out/report_csv`

以上。

