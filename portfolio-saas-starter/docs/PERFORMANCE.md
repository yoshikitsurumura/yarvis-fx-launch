# パフォーマンスと安定性の方針（要点）

- API圧縮: Expressに `compression` を導入し、レスポンスを自動圧縮（小サイズ・高速）。
- 中断可能な通信: Webの `fetchTasks/createTask/toggleTask` にタイムアウトと `AbortController` を追加。
- 揺れの少ない描画: `MiniChart` は `requestAnimationFrame` で描画し、`React.memo` で無駄な再描画を抑制。

## 使い方
- とくに操作は不要。既存のコマンドそのままで恩恵を受けます。
- 通信が10秒以上かかる場合は自動で中断（必要ならコード側で延長可能）。

## 注意
- 変更は後方互換を保つ範囲。API/型は同じままです。
- さらなる最適化（CDN/キャッシュ/SSR等）はMVPの規模と要件に合わせて段階導入します。

