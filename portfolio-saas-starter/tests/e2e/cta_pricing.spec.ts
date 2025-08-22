import { test, expect } from '@playwright/test';

test('CTAと購入ボタンが表示される', async ({ page }) => {
  await page.goto('/');
  // CTA block
  await expect(page.getByRole('heading', { name: 'まずはデモを見る' })).toBeVisible();
  const demoLink = page.locator('a[href*="/docs/"]');
  await expect(demoLink).toHaveAttribute('href', /\/docs\//);
  // Contact mailto
  const mailLink = page.locator('a[href^="mailto:"]');
  await expect(mailLink).toBeVisible();

  // Pricing block
  await expect(page.getByRole('heading', { name: '購入' })).toBeVisible();
  await expect(page.getByRole('button', { name: '購入する' })).toBeVisible();
});

test('ポリシー編集と成果物ギャラリーのセクションが見える', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'ポリシー編集' })).toBeVisible();
  await expect(page.getByRole('heading', { name: '成果物ギャラリー（最新）' })).toBeVisible();
});

