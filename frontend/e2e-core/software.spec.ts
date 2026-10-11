import {test, expect} from '@playwright/test';

test('source-only dashboard preserves navigation and reports absent data honestly', async ({page}) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/');
  await expect(page.getByRole('navigation', {name:'Scientific dashboard views'})).toBeVisible();
  expect((await page.request.get('/api/datasets')).status()).toBe(503);
  await expect(page.locator('main .error')).toContainText(/DESeq2 (has not completed|research data are not installed)/);
  await expect(page.locator('main .error button')).toBeVisible();
  await expect(page.locator('.stats strong')).toHaveCount(0);
  expect(errors).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBeTruthy();
});
