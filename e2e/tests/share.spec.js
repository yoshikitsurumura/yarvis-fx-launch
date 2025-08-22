const { test, expect } = require('@playwright/test');

test('Share page builds v1/v2 links with correct base', async ({ page }) => {
  await page.goto('/lp/share.html');
  const v1 = page.locator('#v1');
  const v2 = page.locator('#v2');
  await expect(v1).toHaveValue(/v=1/);
  await expect(v2).toHaveValue(/v=2/);
  const v1val = await v1.inputValue();
  const v2val = await v2.inputValue();
  // When served locally under /lp/, base should include /lp
  expect(v1val).toMatch(/\/lp\//);
  expect(v2val).toMatch(/utm_campaign=launch/);
});

