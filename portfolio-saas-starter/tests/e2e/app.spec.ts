import { test, expect } from '@playwright/test';

test('トップ表示とタスク追加ができる', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Portfolio SaaS Starter');

  const input = page.getByPlaceholder('新しいタスク');
  await input.fill('e2e task');
  await page.getByRole('button', { name: '追加' }).click();

  // 追加直後は楽観的更新で表示され、その後API応答で置き換わる
  await expect(page.getByText('e2e task')).toBeVisible();
});

