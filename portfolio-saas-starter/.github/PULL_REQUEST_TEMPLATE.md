## 概要
変更内容の要約を簡潔に記載してください。

## 関連Issue
- Closes #

## 変更点
- 

## スクリーンショット / 動作確認
貼れる場合は画像やGIFを添付してください。

## テスト計画
- 実行コマンド: `npm run typecheck`, `npm test`, `npm run build`
- 結果: すべて成功 / 失敗時の詳細

## CI実行について
- コスト安全のため、CI/E2Eはデフォルト停止です。実行する場合はラベル `run-ci`（CI）/`run-e2e`（E2E）を付与してください。もしくは、リポジトリ変数 `CI_ALLOW` / `E2E_ALLOW` を `true` に設定します。

## チェックリスト
- [ ] 影響範囲を確認し、必要な箇所のテストを追加
- [ ] ルートで `npm run typecheck` / `npm test` / `npm run build` が成功
- [ ] ドキュメント（`README.md` や `AGENTS.md`）を必要に応じて更新
- [ ] 破壊的変更がある場合は明記し、移行手順を記載
