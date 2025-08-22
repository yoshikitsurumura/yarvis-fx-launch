const { test, expect } = require('@playwright/test');

test.beforeEach(async ({ page }) => {
  // Make mock succeed deterministically
  await page.addInitScript(() => { Math.random = () => 0.9; });
});

test('Yarvis MVP success shows banner and CTA carries query', async ({ page }) => {
  await page.goto('/yarvis-fe/index.html?v=2&utm_source=test&utm_medium=ci');
  // select first item
  await page.click('#list li >> nth=0');
  await page.click('text=実行（モック）');
  // banner appears
  const banner = page.locator('#success-banner');
  await expect(banner).toBeVisible();
  const href = await banner.locator('a').getAttribute('href');
  expect(href).toContain('/lp/index.html');
  expect(href).toContain('v=2');
  expect(href).toContain('utm_source=test');
  expect(href).toContain('utm_medium=ci');
});

