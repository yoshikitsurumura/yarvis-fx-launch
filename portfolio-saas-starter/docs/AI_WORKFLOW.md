# AI 開発ワークフロー（Gemini CLI 雛形）

このプロジェクトでは、AI を安全に“補助ツール”として使うための雛形を用意しています。Gemini CLI の実体は各自で導入してください（例: `gemini` コマンド）。

## 前提
- 実行許可: コスト安全のため `AI_ALLOW=1` を設定しないと `npm run ai:*` は実行されません
- APIキー: `GEMINI_API_KEY` をセット
- 設定: `.ai/gemini.config.json` を編集（モデル/温度など）

## 代表タスク（例）
- 仕様ドラフト作成: `npm run ai:spec`
- テスト草案生成: `npm run ai:tests`
- 変更レビュー支援: `git add -A && npm run ai:review`（ステージ差分を送る）
- ドキュメント初稿: `npm run ai:docs`

CLI フラグやファイル入力の方式はお使いの Gemini CLI に合わせて `.ai/gemini.config.json` や `package.json` のスクリプトを調整してください。

## プロンプト
- `.ai/prompts/*.md` に役割ごとのテンプレートを用意（spec / tests / review / docs）。
- プロジェクト固有の制約（型、命名、ディレクトリ）は `AGENTS.md` を参照し、プロンプトに踏襲。

## ベストプラクティス
- 最小差分で提案: 「どのファイルのどの行にどう影響するか」を具体化
- セキュリティ/秘匿情報: 環境変数・鍵・個人情報は送らない
- 最終判断は人間: AI 提案は“叩き台”。テストとレビューを通す
