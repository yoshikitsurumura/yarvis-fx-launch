Windows クイックスタート（ローカル実行）

前提
- Windows 10/11
- ブラウザ（Edge/Chrome）
- 任意: Node.js LTS（E2Eテストを動かす場合）

1) フォルダを展開
- `windows_bundle.zip` を任意のフォルダへ展開
- 構成例: `windows_start_here/`, `lp/`, `yarvis-fe/`, `docs/`, `scripts/`, `.github/`

2) フォームURL設定（必須）
- いちばん簡単: `windows_start_here\Set_Form_URL.cmd` をダブルクリック
  - 初回は自動で `lp\config.js` が作成され、メモ帳で開きます
  - `window.LP_FORM_URL = 'https://docs.google.com/forms/d/e/XXXX/viewform';` に差し替えて保存

3) そのまま開く（最速）
- LP: `lp\index.html` をダブルクリック
- やーびす: `yarvis-fe\index.html` をダブルクリック

4) 簡易サーバで開く（推奨）
- `windows_start_here\Run_Server.cmd` をダブルクリック
- ブラウザで:
  - `windows_start_here\Open_LP_v1.cmd` / `Open_LP_v2.cmd`
  - または `windows_start_here\Open_Demo.cmd`

5) 公開後の配布リンク作成（任意）
- 公開URLが `https://<user>.github.io/<repo>/` のとき:
```
make pages-links BASE=https://<user>.github.io/<repo>/
```
（`make` が無い場合は、`scripts\ab_links.py --base <公開URL>` を実行）

6) E2Eテスト（任意）
- Node.js LTS をインストール
```
cd e2e
npm install
npx playwright install chromium
cd ..
py -m http.server 8000
cd e2e
npm test
```

トラブルシュート
- フォームに飛ばない: `lp\config.js` の URL を再確認（末尾 `/viewform`）
- A/Bが切り替わらない: URLに `?v=1` または `?v=2` を付与、もしくはブラウザのサイトデータを削除
- 文字化け: できれば簡易サーバで開く（手順4）
