# リリースチェックリスト（v0.1.0想定）

## 前提
- 依存導入済み: `pip install -r requirements.txt`
- 実行パス: `export PYTHONPATH=src`

## 1) 最終動作確認（ローカルCSV）
- サンプルBT: `make fx-backtest-sample`
- CSV出力: `make fx-export-sample`
- 最適化（期間指定）: READMEのコマンド例どおりに `optimize` 実行
- ベスト再BT: `backtest-with-opt` 実行
- Walk-Forward（期間指定）: READMEどおりに `walkforward` 実行

## 2) 成果物の束ね
- 主要ファイルを `out/final_check_csv/` にコピー
  - `out/report_sample.json`
  - `out/report_sample_csv/` 一式
  - `out/opt_results.json`
  - `out/report_best.json`
  - `out/walkforward.json`

## 3) バージョンとノート
- パッケージ版数: `fxbot.__version__` が `0.1.0` であること
- 変更履歴: `CHANGELOG.md` を確認
- リリースノート: `docs/RELEASE_NOTES_v0.1.0.md` を確認

## 4) タグ付け（任意）
- 例: `git tag v0.1.0 && git push origin v0.1.0`
- GitHub Releases を作成し、上記成果物を添付

## 5) 周知（任意）
- READMEの対象セクション（最適化/Walk-Forward）に変更点が反映済み
- LP/デモに誘導する場合は `docs/HANDOFF.md` の導線を案内

以上。
