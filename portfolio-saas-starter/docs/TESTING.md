# Testing Guide

本プロジェクトは npm workspaces + Vitest を使用します。API と Web で共通の実行方法に揃えています。

## 実行コマンド
- 全体テスト: `npm test`
- 型チェック: `npm run typecheck`
- 個別（API）: `npm test -w @app/api`
- 個別（Web）: `npm test -w @app/web`
- ウォッチ（例・Web）: `npm test -w @app/web -- --watch`

## 配置と命名
- API: `apps/api/tests/*.test.ts`
- Web: `apps/web/src/**/*.test.tsx`（コンポーネント近接配置を推奨）
- テスト名は「対象機能 + 条件 + 期待結果」を意識（例: `tasks toggling updates UI`）

## 目的別の方針
- ユニット（関数・小さなコンポーネント）: 入出力とエッジケースを重点
- 統合（API ルート/サービス層）: 正常系と代表的異常系（400/404）を1本ずつ
- UI: React Testing Library を用い、ユーザー視点（テキスト/ロール）で検証

## よくあるミスと回避
- 非同期: `await` を忘れず、`findBy*` を活用
- 時刻/ID依存: 固定値/モックでテストを安定化
- I/O: API の `.data` はテスト中に汚さない（モック or 一時ディレクトリ推奨）

## トラブルシュート
- 型の不一致: `npm run typecheck` でまず確認
- 失敗原因の特定: 個別ワークスペースで `-w` を使って範囲を絞る

