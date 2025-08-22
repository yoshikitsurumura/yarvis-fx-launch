ハンドオフ（全体概要・すぐ使える要点）

目的
- 3コンポーネント（LP・やーびすFE・CI/自動化）を、誰でも回せる状態で引き渡す。

構成（完成度: MVP）
- LP (`lp/`): 依存ゼロ静的サイト。A/B切替、UTM付与、埋め込みフォーム、診断ミニフォーム。
- やーびすFE (`yarvis-fe/`): 一覧→詳細→実行（モック）→成功バナー→LP誘導。A/B/UTM引継ぎ。
- CI/自動化 (`.github/workflows/`):
  - `pages.yml`: `lp/`をGitHub Pagesに自動公開（SummaryにA/Bリンク出力）
  - `e2e.yml`: LPとやーびすのE2Eテスト（Playwright）
  - `preview.yml`: PR時に`lp/`/`yarvis-fe/`をZIP化してArtifact出力

運用のキモ（売上に直結）
- 北極星: フォーム送信数/月。A/Bで「見出し→CTA→事例→価格」の順に1要素ずつ改善。
- 配布リンク: PagesデプロイSummary or `make pages-links BASE=...` で即作成。
- 相談導線: LPとやーびすFEの両方にCTA。UTM/variantを自動付与。

最初の2手（必須）
1) フォームURL設定: `lp/config.example.js` → `lp/config.js` にコピーし、
   `window.LP_FORM_URL = 'https://docs.google.com/forms/d/e/XXXX/viewform'`
2) GitHub Pages初回有効化: Settings→Pages→Source = GitHub Actions

すぐ実行（ローカル）
- LP: `lp/index.html?v=2&utm_source=lp&utm_medium=web&utm_campaign=launch`
- やーびす: `yarvis-fe/index.html`
- きれいに表示する場合: `py -m http.server 8000` で `http://localhost:8000/` を使用。

ドキュメント索引
- Windowsクイックスタート: `docs/QUICKSTART_WINDOWS.md`
- 運用チェック: `docs/OPS_CHECKLIST.md`
- 販売計画: `docs/SALES_PLAN.md`
- フォーム連携/プレフィル: `docs/LP_PREFILL.md`

補助ツール
- `scripts/ab_links.py` / `make pages-links BASE=...`: A/Bリンク自動生成

よくある質問（抜粋）
- A/Bが固定される: `localStorage`で保持。クエリ`?v=1|2`で上書き可。
- フォームでUTMが見えない: Googleフォームの回答シートでクエリ列を確認。必要ならプレフィルに移送。

