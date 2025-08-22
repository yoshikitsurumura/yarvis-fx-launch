# @app/api

Express ベースのシンプルなタスク API。

## スクリプト
- 開発: `npm run dev -w @app/api`
- ビルド: `npm run build -w @app/api`
- 起動: `npm start -w @app/api`
- テスト: `npm test -w @app/api`

## エンドポイント
- `GET /health` ヘルスチェック
- `GET /tasks` タスク一覧
- `POST /tasks` タスク作成 `{ title: string }`
- `PATCH /tasks/:id` 更新 `{ title?: string; done?: boolean }`
- `DELETE /tasks/:id` 削除

