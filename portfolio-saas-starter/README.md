# Portfolio SaaS Starter (TypeScript Monorepo)

[![CI](https://github.com/your-org/your-repo/actions/workflows/ci.yml/badge.svg)](./.github/workflows/ci.yml)

フロントエンド(React + Vite + Vitest) と API(Express) を同居させた TypeScript モノレポのスターターです。共通型パッケージを介して型安全に連携し、テスト、Docker、CI まで一通り揃っています。ポートフォリオにそのまま使える構成を意識しています。

## 特徴
- モノレポ構成: `apps/web`, `apps/api`, `packages/types`
- 型共有: API とフロントで同一の型を利用
- テスト整備: Vitest + @testing-library（web）、API はユニット中心
- Vite + React の高速開発体験
- Express API のシンプルな CRUD 実装（JSON 永続化）
- Docker / docker-compose での起動例
- GitHub Actions による CI（lint / typecheck / test / build）

## セットアップ（最短3ステップ）
```
cd portfolio-saas-starter
npm install --workspaces
make dev   # ない場合: npm run dev
```

## 開発（ローカル）
- 同時起動: `make dev`（または `npm run dev`）
- 個別起動: `npm run dev -w @app/api` / `npm run dev -w @app/web`

### Webの任意設定（デモ/お問い合わせ）
`apps/web/.env.development.example` を参考に `.env.development` を作成:
```
VITE_DEMO_URL=/docs/SALES_DEPLOY.md
VITE_CONTACT_EMAIL=you@example.com
```

## ビルド
- すべて: `npm run build --workspaces`（または各ワークスペースで個別に実行）

## テスト
- すべて: `npm test --workspaces`
- Web 単体: `npm test -w @app/web`
- API 単体: `npm test -w @app/api`
 - E2E: `npm run e2e`

詳細手順は `docs/TESTING.md` を参照してください。

## Docker
```
docker compose up --build
```
- Web: http://localhost:5173
- API: http://localhost:3000

## Netlify デプロイ
このリポジトリには Netlify 用の `netlify.toml` を同梱しています。リポジトリをNetlifyに接続するだけで、以下の設定でビルドされます。

- Base: `portfolio-saas-starter`
- Build command: `npm install --workspaces && npm run build -w @app/web`
- Publish directory: `apps/web/dist`
- Node: `20`

任意の環境変数
- `VITE_DEMO_URL`（デモ動画/ページのURL）
- `VITE_CONTACT_EMAIL`（お問い合わせ宛先）
- `VITE_STRIPE_PRICE_ID`（Checkoutのprice ID。テスト例: `price_test`）
- `STRIPE_SECRET_KEY`（本番/テスト用のSecret。設定するとNetlify関数がStripe連携でCheckoutセッションを作成）

## ディレクトリ構成
```
portfolio-saas-starter/
  apps/
    api/
    web/
  packages/
    types/
  docs/
  .github/workflows/
  tests/e2e/

## 参考ドキュメント
- コスト/安全に関する注意: `docs/COSTS_AND_SAFETY.md`
- AIワークフロー: `docs/AI_WORKFLOW.md`
- 開発ログ: `docs/DEVELOPMENT_LOG.md`
- 自然言語開発とツール連携: `docs/NL_DEV_AND_TOOLS.md`
- 販売ロードマップ: `docs/GO_TO_MARKET.md`

## 補助UI（やーびす関連）
- ポリシー編集: Webのトップ画面「ポリシー編集」で許可ドメイン/アクション・上限を保存（APIの`/automation/config`に反映）
- 成果物ギャラリー: Webの「成果物ギャラリー（最新）」で `/files/automation/*` を一覧表示（APIが`.data/automation`を静的配信）
```

## ライセンス
MIT
