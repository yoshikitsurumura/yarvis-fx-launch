LPのGoogleフォーム連携（プレフィル）

目的
- LPのCTAからGoogleフォームに遷移する際、計測用のクエリと簡易診断の回答を自動付与します。

実装ポイント
- ファイル: `lp/ab.js`
- 置換: 実際のGoogleフォームURLの設定方法は2通り。
  1) 直接: `lp/ab.js` の `FORM_URL` を差し替え
  2) 外部設定（推奨）: `lp/config.example.js` を `lp/config.js` にコピーし、`window.LP_FORM_URL` を設定
- 付与クエリ: `utm_source, utm_medium, utm_campaign, variant, note`
  - `note` は「導入可否の簡易診断」で選んだ3項目を `診断:項目1/項目2/項目3` の形式で渡します。

Googleフォームでの項目マッピング（任意）
1) フォームに「備考」や「診断メモ」等の自由記述を1つ用意
2) Googleフォームの「事前入力したURL」を生成して、`entry.xxxxxx=__NOTE__` の形でテンプレートURLを取得
3) `lp/ab.js` の `buildFormUrl()` で `note` を該当 `entry.xxxxxx` にコピーする処理へ変更

例（疑似コード）
```
// const TEMPLATE_URL = 'https://docs.google.com/forms/d/e/.../viewform?usp=pp_url&entry.12345=';
// const note = u.searchParams.get('note');
// if (note) u.searchParams.set('entry.12345', note);
```

埋め込み
- クエリに `embed=1` を付けると、LP内の `#form-embed` にフォームをiframeとして表示します。
- 例: `lp/index.html?embed=1`

A/Bテスト
- バリアントは `?v=1|2` で指定。指定がない場合は初回アクセスでランダム割り当てし、`localStorage` に保持します。
- 記録: フォームに `variant` をクエリで付与します。
