# 自然言語開発とツール連携の方針（初心者向け）

- ねらい: 自然言語（日本語）で仕様やテスト案を素早く作り、最終判断は人間＋テストで担保。
- コスト: 外部AIやCIは課金の可能性あり。必ず `docs/COSTS_AND_SAFETY.md` を確認してから有効化。

## 使い方（AI補助）
- 仕様叩き台: `npm run ai:spec`
- テスト草案: `npm run ai:tests`
- 差分レビュー補助: `git add -A && npm run ai:review`
- ドキュメント案: `npm run ai:docs`
- 設定: `.ai/gemini.config.json` と `.ai/prompts/*`（Gemini CLI を想定）

## フラグとテレメトリ（費用不要・デフォルト無効）
- 機能フラグ: `@pkg/flags` で `FEATURE_*` を切替
  - 例: `VITE_FEATURE_CHART=1` でグラフを表示（Web）
- テレメトリ: `@pkg/telemetry` は Opt-in のみログ（送信なし）
  - Web: `VITE_TELEMETRY_OPT_IN=1` でコンソールにイベント表示
  - API: `TELEMETRY_OPT_IN=1` でサーバ側も有効にできる設計（現状未使用）

## 開発フロー（おすすめ）
1) 仕様をAIで下書き→読み合わせ→小さく実装
2) テスト草案をAIで作成→必要箇所を手直し→`npm test` / `npm run e2e`
3) PRに説明とスクショ、コストに影響する変更は明記

