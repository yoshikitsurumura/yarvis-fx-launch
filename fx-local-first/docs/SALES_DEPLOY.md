# 販売経路（作る→見せる→課金）ドキュメント

目的: LP/デモ/課金の最短経路をゼロコスト優先で整備し、誰でも同じ手順で再現できるようにします。

## 1. デモ動画（短尺）収録と公開
- 方針: 15–30秒、無音or最小BGM、1080p/30fps、GIFも用意
- 収録案:
  - macOS: QuickTime(画面収録) → `ffmpeg`でmp4最適化＆gif生成
  - Linux: `obs-studio` or `peek` でgif直収録（軽量）
- 変換例（mp4→gif、短尺向け）:
  - `ffmpeg -i demo.mp4 -vf "fps=15,scale=960:-1:flags=lanczos" -t 00:00:20 demo.gif`
- 公開先の優先度:
  1) GitHub Releases（リポジトリ内で完結）
  2) README/LPに埋め込み（`/docs/assets`にgifを置く）
- 作業チェックリスト:
  - [ ] 主要ユースケースを1つに絞る（ワンクリックデモ推奨）
  - [ ] 20秒以内で完結
  - [ ] mp4 + gif を両方用意
  - [ ] README/LPへ埋め込み

## 2. 無料デプロイ先の選定とデプロイ
- 候補と特徴:
  - Cloudflare Pages: 無料枠広め、独自ドメイン簡単、静的に強い
  - Netlify: フォームやFunctionsが容易、設定簡単
  - Vercel: SSR/Edgeに強い、Next系と相性
- 想定構成: `portfolio-saas-starter/apps/web` を静的ホスティングで公開（APIは不要ならモックで十分）
- Cloudflare Pages 例:
  - リポジトリ接続 → Framework: None → Build command: `npm run build -w @app/web` → Build output: `apps/web/dist`
  - 環境変数（必要時）: `VITE_*` をPages側に設定
- Netlify 例（本リポは `netlify.toml` 同梱）:
  - リポジトリを接続するだけで自動検出
  - Base: `portfolio-saas-starter`
  - Build: `npm install --workspaces && npm run build -w @app/web`
  - Publish: `apps/web/dist`
  - 任意の環境変数（UIのCTA向け）
    - `VITE_DEMO_URL`（デモURL）
    - `VITE_CONTACT_EMAIL`（問い合わせ先）
- Vercel 例:
  - Root: リポジトリ直下 → `npm i --workspaces` → Build command: `npm run build -w @app/web` → Output dir: `apps/web/dist`

## 3. Stripe サンドボックス初期導入
- 目的: LP→チェックアウトの最小動線（テスト用）
- 手順:
  1) Stripeダッシュボードでテストキーを取得（Secret/Public）
  2) `.env.local` に以下を定義（web側）
     - `VITE_STRIPE_PUBLIC_KEY=pk_test_...`
  3) 決済生成はAPIが必要（最低限のFunction/APIを別途用意）
     - 本リポは Netlify Functions のスタブを同梱
     - `portfolio-saas-starter/netlify/functions/create-checkout-session.js`
  4) サーバー側環境変数（Netlify → Site settings → Environment variables）
     - `STRIPE_SECRET_KEY=sk_test_...`
- API擬似実装方針（疑似コード）
  - `POST /.netlify/functions/create-checkout-session` に `priceId` と `success_url`/`cancel_url` を渡す
  - （スタブ）固定のテストURLを返却 → フロントでリダイレクト
  - （本番）`STRIPE_SECRET_KEY` がある場合はStripe SDKを利用して `checkout.sessions.create` を実行（同梱の関数が自動で切替）

### 参考: 料金IDの扱い
- `VITE_STRIPE_PRICE_ID`（Web側env）にCheckout用の`price_xxx`を設定
- 数量はUI側から指定可能（現状は1固定、必要に応じて拡張）
  - レスポンスで `url` を返却 → フロントで `window.location = url`
- 注意:
  - テストカードのみ使用（`4242 4242 4242 4242` など）
  - 法務ドキュメント（下記）のリンクをLPに明記

## 4. LPのCTA/導線の最小改善
- CTAボタン: 「デモを見る」「無料で試す」 の2本立て
- デモ: 上記のデモgif/mp4に直リンク
- 連絡: メールリンク or 簡易フォーム（Netlify Formsなど）

## 5. チェックリスト（Doneの定義）
- [ ] デモ動画（mp4/gif）が `docs/assets/` に配置され、README/LPから参照
- [ ] Cloudflare/Netlify/Vercel のいずれかでLPが公開
- [ ] Stripeテストキーと最小APIの雛形が整理され、手順が `docs/SALES_DEPLOY.md` に記載（Netlify Functionsスタブ動作）
- [ ] 利用規約・プライバシーのテンプレを配置し、LPからリンク
