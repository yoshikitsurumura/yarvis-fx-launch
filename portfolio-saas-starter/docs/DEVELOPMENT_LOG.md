# 開発ログ（やったこと/やること）

本ログは「いま何をやって、次に何をするか」を短く残すための運用メモです。PRにも同様の要約を入れてください。

## 直近の作業（Done）
- ルートに CI（lint/typecheck/test/build）と E2E（Playwright）を追加
- Web/API のユニット/統合テスト整備、トグル不具合修正
- Lint/Prettier/EditorConfig/Husky（pre-commit）導入
- Docker（dev/prod）と VSCode タスク/起動
- AI補助の雛形（docs/AI_WORKFLOW.md, .ai/*）
- API Seed スクリプトと API ドキュメント
- コスト注意ドキュメント（docs/COSTS_AND_SAFETY.md）
- パフォーマンス: API圧縮（compression）、中断可能fetch、MiniChart の描画最適化

- Automation: ドライラン検証API(`/automation/dry-run`)と実行時のバリデーションを追加
- Web: プラン作成後に自動ドライラン、エラー/警告のUI表示、NG時は実行ボタン抑止
- Tests: APIの検証テストとE2Eに「プラン→ドライラン→実行→表示」を追加
- CI: `run-ci`/`run-e2e`ラベルでCI/E2E実行を許可（varsがfalseでも）
- Docs: API/E2E/LPドキュメントを更新、CHANGELOG_LITE自動更新ワークフローを追加

## 次にやること（To Do）
- 最小E2Eの観点追加（エラーケース・遅延時のUI）
- ESLintルールの軽度強化（未使用importなどは警告運用）
- READMEへ「コスト注意（COSTS_AND_SAFETY.md）」のリンクを明示
 - API応答のETag/Cache制御の検討（規模次第）

## ルール
- 小さく進めて、小さくマージ。大きくなるときは先に仕様（`npm run ai:spec`）で叩き台を作成
- 費用が発生する設定（CI時間・AI・外部API）は、事前にコスト確認
