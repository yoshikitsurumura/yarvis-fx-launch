# コストと安全に関する注意

このプロジェクトでは、外部サービスやCI/CDを利用できます。お金が発生し得るポイントを明確にし、各自の判断で有効化してください。

## 料金が発生し得るもの
- GitHub Actions: リポジトリのプラン/分数に応じて課金。私用・私有Repoは特に注意。
- Gemini API 等のAIサービス: APIキーの利用に応じて課金。`GEMINI_API_KEY` を設定する前に料金表を確認。
- 外部API/クラウド: 今後導入する場合は必ず料金と上限を確認。

## デフォルト動作
- このリポジトリは、AIコマンドやE2Eはローカル実行を前提。外部課金が直ちに発生する設定にはしていません。
- GitHub Actionsのワークフローは有効化済みですが、実行はGitHub側の設定/権限に従います。

## GitHub Actions のコスト管理（実践）
- 変数でガード（推奨）: リポジトリ変数 `CI_ALLOW`/`E2E_ALLOW` を `true` にするまでCI/E2Eは実行しません。
  - 手順: GitHub → Settings → Secrets and variables → Actions → Variables
  - `CI_ALLOW=true` で通常CI、`E2E_ALLOW=true` でE2Eが有効
- 実行を絞る: docs/Markdown 変更は `paths-ignore` でスキップ済み。
- 無駄な並列を止める: `concurrency` で古い実行を自動キャンセル。
- 手動実行: `workflow_dispatch` を用意。必要時のみ実行も可。
- さらに抑えるには:
  - push のトリガーを main のみに限定（PR中心運用）
  - 自前ランナー（self-hosted）を使用（GitHub分数ではなく自前リソース）

## 推奨運用
- APIキーはリポジトリに含めない（`.env*` を使用）。
- まずはローカルで動作確認 → 必要に応じてCIを有効化。
- 料金の上限/クォータを設定し、ダッシュボードで利用量を確認。

## AI スクリプトのコスト管理（ローカル）
- `npm run ai:*` は `AI_ALLOW=1` を設定しない限り実行しません（安全側）。
- 例: `AI_ALLOW=1 npm run ai:spec`

## 相談の仕方（初心者向け）
- 使う前に「これにお金かかる？」と一言確認してください。設定や代替案を提案します。
