import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { localPage, ORIGIN } from './home-family-local-fixture.mjs';

const browser = await chromium.launch({ headless: true });
try {
  const { context, page } = await localPage(browser);
  await page.goto(ORIGIN + '/', { waitUntil: 'load' });

  assert.equal(await page.evaluate(() => sessionStorage.getItem('dp-intro-seen')), null);
  assert.equal(await page.locator('[data-intro]').isVisible(), true);
  assert.equal(await page.locator('main').getAttribute('inert'), '');

  const firstPreload = await page.locator('link[rel="preload"][as="image"]').first().getAttribute('href');
  assert.match(firstPreload, /hero-tinta-poster\.webp/);

  await page.locator('[data-intro-enter]').click();
  await page.waitForFunction(() => document.querySelector('[data-intro]')?.hidden);
  assert.equal(await page.evaluate(() => sessionStorage.getItem('dp-intro-seen')), '1');
  assert.equal(await page.locator('main').getAttribute('inert'), null);
  assert.equal(await page.evaluate(() => document.documentElement.classList.contains('intro-lock')), false);

  await page.reload({ waitUntil: 'load' });
  await page.locator('[data-editorial-home-flow]').waitFor();
  assert.equal(await page.locator('[data-intro]').isHidden(), true);
  assert.equal(await page.locator('main').getAttribute('inert'), null);

  const returningPreload = await page.locator('link[rel="preload"][as="image"]').first().getAttribute('href');
  const heroSource = await page.locator('.yale-lead__media img').getAttribute('src');
  assert.equal(new URL(returningPreload, ORIGIN).pathname, new URL(heroSource, ORIGIN).pathname);

  await context.close();
  console.log('PASS home-intro-session-journey');
} finally {
  await browser.close();
}