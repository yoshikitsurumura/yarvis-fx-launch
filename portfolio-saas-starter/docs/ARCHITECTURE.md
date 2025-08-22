# アーキテクチャ概要（初心者向け）

- モノレポ構成
  - `apps/web`: フロント（Vite + React）。UI・サービス層（API呼び出し）・小さなUI部品。
  - `apps/api`: サーバ（Express）。`routes/`にHTTPルート、`storage/`に簡易DB（JSON）。
  - `packages/types`: 共有の型定義。WebとAPIで同じ型を使いバグを減らす。

- 起動とやり取り
  - Webの開発中はViteが`/api`へのリクエストをAPI（http://localhost:3000）に転送。
  - 本番や別環境は `VITE_API_BASE` を設定してAPI先を切替可能。

- コードの入口
  - Web: `apps/web/src/modules/App.tsx`（画面の中心）。
  - API: `apps/api/src/routes/tasks.ts`（タスクのCRUD）。
  - 型: `packages/types/src/index.ts`（Taskなど）。

- テスト
  - Web: コンポーネントやサービス層のテスト（Vitest + Testing Library）。
  - API: ルート統合テスト（supertest）とストレージ単体テスト。

- 変更のコツ（安全）
  1) 型を先に変える → 2) API/WEBをあわせる → 3) テストを通す。
  失敗したらコミット前のフックやCIが早めに教えてくれる。

