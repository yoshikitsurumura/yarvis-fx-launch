あなたへの指示書（最小の手順）

目的
- A/B運用で問い合わせ（MQL）を増やすための、今日から実行できるタスク。

今日やること（30分）
1) フォームURL設定（必須）
   - `lp/config.example.js` を `lp/config.js` にコピー
   - `window.LP_FORM_URL = 'https://docs.google.com/forms/d/e/XXXX/viewform'` に差し替え
2) Pages有効化（初回のみ）
   - GitHub → リポジトリ → Settings → Pages → Source: GitHub Actions
3) push/PR作成
   - Actionsで `e2e` が実行、`pages` で公開、SummaryにA/Bリンクが出ます

明日やること（45分）
- 公開A/Bリンク（v1/v2）を2–3チャネルへ配布
- `docs/OPS_CHECKLIST.md`の台帳に「日付/クリック/送信/メモ」を記録

今週やること（1時間）
- 価格 or 事例を1つだけ追記（数字1つ）
- A/Bの勝ちを採用し、次の1要素だけ改善（見出し→CTA→事例→価格の順）

便利コマンド
- A/Bリンク生成: `make pages-links BASE=https://<pages-url>/`
- ローカルサーバ: `py -m http.server 8000`

相談導線の要点
- LPとやーびすの両方にCTAあり（UTM/variant自動付与）
- フォーム埋め込みは `&embed=1` でページ内完結も可能

困ったら
- Windows起動手順: `docs/QUICKSTART_WINDOWS.md`
- プレフィル: `docs/LP_PREFILL.md`
- 改善Issueテンプレ: `.github/ISSUE_TEMPLATE/lp_copy.yml`

