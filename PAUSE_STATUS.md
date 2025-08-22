# 停止時点サマリ（3プロジェクト横断）

- 日時: 手動再開まで一時停止
- 対象: 1) GitHub Actions（省コスト運用） 2) 販売経路（作る→見せる→課金） 3) やーびす（自動PC操作）

## 全体サマリ（進捗・優先度）
- 優先度（合意案）: 1) Actions → 2) 販売 → 3) やーびす
- 進捗見立て（提供値をベースに反映）:
  - GitHub Actions: 90%
  - 販売経路: 70%（本ブランチ実装で一部前進: Netlify設定/CTA/購入導線/法務テンプレ）
  - やーびす: 80%（MVP完了＋安全/UX補強を追加）

## 現在の状態
### 1) GitHub Actions（省コスト運用）
- 状態
  - `.github/workflows/ci.yml` 追加: ラベル駆動（`run-ci`/`run-e2e`）、`paths-ignore`、`concurrency`、`workflow_dispatch`対応
  - CHANGELOG-lite: 最新コミットに紐づくPRを `actions/github-script` で取得→Job Summary＋Artifactに出力
- 関連ファイル
  - ルート: `.github/workflows/ci.yml`
- メモ
  - リポジトリでラベル運用（`run-ci`/`run-e2e`）が前提

### 2) 販売経路（作る→見せる→課金）
- 状態
  - Netlify構成: `netlify.toml`（Base/Build/Publish/Functions/Node）
  - 決済導線: Netlify Functionsスタブ＋`STRIPE_SECRET_KEY` で本番切替
  - Web UI: CTA（デモ/メール）・購入ボタン
  - 法務テンプレ配置済み
- 関連ファイル
  - 関数: `portfolio-saas-starter/netlify/functions/create-checkout-session.js`
  - 依存: `portfolio-saas-starter/package.json`（`stripe`）
  - Web: `apps/web/src/ui/Cta.tsx`（既定`/demo.svg`）, `apps/web/src/ui/Pricing.tsx`
  - デモ置き場: `apps/web/public/demo.svg`
  - Docs: `docs/SALES_DEPLOY.md`, `docs/LEGAL/TERMS_TEMPLATE.md`, `docs/LEGAL/PRIVACY_TEMPLATE.md`, 両README

### 3) やーびす（自動PC操作）
- 状態
  - API: `/automation/config`（GET/POST）、`/automation/artifacts`（GET）、`/files`静的配信
  - Web UI補強: ポリシー編集UI、成果物ギャラリー、ワンクリックデモ（既存）
- 関連ファイル
  - API: `apps/api/src/routes/automation.ts`, `apps/api/src/config/automation.ts`
  - Web: `apps/web/src/ui/PolicyEditor.tsx`, `apps/web/src/ui/ArtifactsGallery.tsx`, `apps/web/src/modules/Automation.tsx`

## 未実施（保留）
- GitHub Actions: CHANGELOG抽出の精度改善（直近マージPRのみ。必要ならGitHub API利用へ拡張）
- 販売経路: Netlifyへの接続と初回デプロイ（公開URL未発行）
- 販売経路: デモ動画(mp4/gif)の差し替え（現状 `/demo.svg` プレースホルダ）
- やーびす: 限定ドメインでのヘッドレス実機操作（録画/スクショ）、許可セレクタ/アクション上限の設定ファイル化（詳細）

## 再開時の最短手順
1) NetlifyでリポジトリをImport（`netlify.toml`により自動設定）
2) 必要なら環境変数を追加（Site settings → Environment variables）
   - `VITE_DEMO_URL`（未設定なら`/demo.svg`）
   - `VITE_CONTACT_EMAIL`
   - `VITE_STRIPE_PRICE_ID`
   - `STRIPE_SECRET_KEY`（設定でStripe本番フロー有効）
3) Deploy実行 → 付与された公開URLを共有（導線の最終チェックを実施）

（任意）Actionsの検証
- PRに`run-ci`ラベルを付与 → CI起動確認
- `main`へマージ（または`workflow_dispatch(force=true)`）→ CHANGELOG-liteがSummary/Artifact出力されることを確認

## ローカルでの確認（任意）
- API: `npm run dev -w @app/api`（http://localhost:3000）
- Web: `npm run dev -w @app/web`（http://localhost:5173）
- E2E: `cd portfolio-saas-starter && npm run e2e`

## つまづき対処メモ
- Build設定が噛まない: Site側で手動設定を上書きしていればリセット（`netlify.toml`に従う）
- デモリンク不通: `VITE_DEMO_URL`の先の存在を確認（未設定なら`/demo.svg`は常に存在）
- Stripeエラー: `STRIPE_SECRET_KEY`/`price_xxx`の不一致を確認（まずテストキー/テストpriceで検証）

（やーびす）
- ドライランでNG時はポリシー（ドメイン/アクション）とセレクタ指定を見直し
- 成果物は `.data/automation/<timestamp>/` に保存 → Webの「成果物ギャラリー」から参照
