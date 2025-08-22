import { test, expect } from '@playwright/test';

test('自動操作デモ: プラン→実行→表示', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { level: 2, name: '自動操作（やーびす MVP）' })).toBeVisible();

  // プラン作成
  await page.getByRole('button', { name: 'プラン作成' }).click();
  await expect(page.getByText('プラン:')).toBeVisible();

  // ドライラン結果表示
  await expect(page.getByText('ドライラン検証:')).toBeVisible();

  // 実行
  await page.getByRole('button', { name: '実行' }).click();
  await expect(page.getByText('結果:')).toBeVisible();
  await expect(page.getByText('Executed')).toBeVisible();
});

test('ワンクリックデモで成果物が表示される', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('button', { name: 'ワンクリックデモ' })).toBeVisible();
  await page.getByRole('button', { name: 'ワンクリックデモ' }).click();
  await expect(page.getByText('結果:')).toBeVisible();
  await expect(page.getByText('擬似スクリーンショット:')).toBeVisible();
});
