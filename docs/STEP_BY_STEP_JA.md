# 手順書（どこに何があるか＋やる順番）

このドキュメントだけ見れば、設定→公開→配布まで迷わず進められます。

## まずこれ（最短3分）
1) フォームURL設定（必須）
   - 開く: `lp/config.example.js`
   - コピーして新規作成: `lp/config.js`
   - 1行だけ編集:
     - `window.LP_FORM_URL = 'https://docs.google.com/forms/d/e/XXXX/viewform'`
2) GitHub PagesのスイッチON（初回のみ）
   - GitHub → 対象リポジトリ → `Settings` → `Pages` → `Source: GitHub Actions`
3) 公開（自動）
   - `main` に push（またはPR） → Actionsが走り、LPが公開されます
   - 画面: GitHub → `Actions` → `deploy-pages` → Summary に A/B リンクが表示

## リポジトリ地図（最重要だけ）
- `windows_start_here/`（Windows用の入口フォルダ：ダブルクリックでOK）
  - `Set_Form_URL.cmd`: フォームURL設定（初回は自動で `lp\config.js` を作成）
  - `Run_Server.cmd`: 簡易サーバ起動（推奨）
  - `Open_LP_v1.cmd` / `Open_LP_v2.cmd`: LPを開く（v1/v2）
  - `Open_Demo.cmd`: 体験画面（やーびす）を開く
  - `Open_Demo_API.cmd`: 体験画面（静的APIモード）を開く
  - `Open_Share.cmd`: 公開後の配布リンク（v1/v2）を表示してコピー
- `lp/`
  - `index.html`: LP本体（A/B切替、フォーム埋め込み、診断）
  - `ab.js`: A/BとUTM付与のロジック
  - `config.example.js`: フォームURLの設定テンプレ（→ `config.js` にコピーして使う）
  - `style.css`: 見た目
  - `robots.txt` / `sitemap.xml` / `favicon.svg`: 公開時のSEO/アイコン（必要に応じ差し替え）
- `yarvis-fe/`
  - `index.html`/`app.js`/`style.css`: 体験用MVP（一覧→詳細→実行→成功バナー→LP）
- `.github/workflows/`
  - `pages.yml`: LPをGitHub Pagesへ自動公開（Summaryに配布リンク）
  - `e2e.yml`: LP/やーびすのE2Eテスト
  - `preview.yml`: PRで `lp/` と `yarvis-fe/` のZIPをArtifact化
  - `bundle.yml`: Windows用ZIPをArtifact化
- `docs/`
  - `HANDOFF.md`: 全体要約（何ができるか）
  - `INSTRUCTIONS_FOR_YOU.md`: 今日/明日/今週にやること
  - `QUICKSTART_WINDOWS.md`: Windowsでの最短起動手順
  - `OPS_CHECKLIST.md`: 日次・週次の運用チェック
  - `SALES_PLAN.md`: 2週間の販売計画
  - `LP_PREFILL.md`: フォームのプレフィル（備考に診断メモを入れる）
- `scripts/`
  - `ab_links.py`: 公開URLから v1/v2 の配布リンクを自動生成
- `out/windows_bundle.zip`: Windowsへ持っていく用のZIP（存在しない場合はCIのArtifactからDL）

## 作業ごとの手順
● フォームURLを設定する（必須）
1) `lp/config.example.js` → `lp/config.js` を作る
2) `window.LP_FORM_URL = 'https://docs.google.com/forms/d/e/XXXX/viewform'` を自分のURLに

● ローカルで確認する
- すぐ見るだけ: `lp/index.html` と `yarvis-fe/index.html` をダブルクリック
- きれいに表示: PowerShell で `py -m http.server 8000` →
  - `http://localhost:8000/lp/index.html?v=1`
  - `http://localhost:8000/yarvis-fe/index.html`

● 公開（GitHub Pages）
1) 初回だけ `Settings → Pages → Source: GitHub Actions`
2) `main` に push（またはPR）
3) `Actions → deploy-pages` のSummaryに A/B リンクが表示
   - もしくは `lp/share.html`（Windowsなら `Open_Share.cmd`）で自動生成・コピー
   - 参考: `lp/robots.txt` の `Sitemap:` を公開URLに直しておくと◎

● 配布リンクを自動生成する
- 公開URLが `https://<user>.github.io/<repo>/` のとき:
  - `make pages-links BASE=https://<user>.github.io/<repo>/`
  - もしくは `python scripts/ab_links.py --base https://<user>.github.io/<repo>/`

● やーびすMVPの使い方
- `yarvis-fe/index.html` を開く → 左の一覧から選ぶ → 「実行（モック）」
- 成功すると上にバナーが出て、LPへ行けます（A/B・UTMも引き継ぎ）
- 静的APIモードで試す: `yarvis-fe/index.html?api=1`（または `windows_start_here\Open_Demo_API.cmd`）

● E2Eテスト（任意）
- ローカル: Node.js を入れて `cd e2e && npm install && npx playwright install chromium`
- `py -m http.server 8000` を起動 → `cd e2e && npm test`
- CI: push/PRで自動実行（`.github/workflows/e2e.yml`）

## トラブルシュート
- フォームに飛ばない → `lp/config.js` のURLが正しいか（`/viewform`まで入っているか）
- A/Bが切り替わらない → URLに `?v=1` か `?v=2` を付ける（またはブラウザのサイトデータ削除）
- 文字が崩れる/相対パスがおかしい → 簡易サーバで開く（`py -m http.server 8000`）

## よく使うコマンド（メモ）
- ローカルサーバ: `py -m http.server 8000`
- 配布リンク作成: `make pages-links BASE=https://<user>.github.io/<repo>/`
