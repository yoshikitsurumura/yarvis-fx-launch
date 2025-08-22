const { test, expect } = require('@playwright/test');

test.beforeEach(async ({ page }) => {
  // Avoid real external navigation by capturing URL
  await page.addInitScript(() => {
    const _assign = window.location.assign.bind(window.location);
    Object.defineProperty(window.location, 'assign', {
      value: (url) => { window.__lp_last_cta = url; }, configurable: true
    });
    Object.defineProperty(window.location, 'href', {
      set: (url) => { window.__lp_last_cta = url; }, configurable: true
    });
  });
});

test('LP v2 shows sales-focused headline and CTA builds URL', async ({ page }) => {
  await page.goto('/lp/index.html?v=2&utm_source=test&utm_medium=ci&utm_campaign=ab');
  await expect(page.locator('#hero-title')).toHaveText(/売上に直結|成長を加速/);
  await page.click('#cta-main');
  const url = await page.evaluate(() => window.__lp_last_cta);
  expect(url).toBeTruthy();
  expect(url).toContain('utm_source=test');
  expect(url).toContain('utm_medium=ci');
  expect(url).toContain('utm_campaign=ab');
  expect(url).toContain('variant=v2');
});

test('Variant persists without explicit v query', async ({ page }) => {
  await page.goto('/lp/index.html?v=1');
  await expect(page.locator('#hero-title')).toHaveText(/工数|手作業/);
  // revisit without v param
  await page.goto('/lp/index.html');
  await expect(page.locator('#hero-title')).toHaveText(/工数|手作業/);
});

test('Embed mode shows iframe', async ({ page }) => {
  await page.goto('/lp/index.html?embed=1');
  await expect(page.locator('#form-embed iframe')).toHaveCount(1);
});

