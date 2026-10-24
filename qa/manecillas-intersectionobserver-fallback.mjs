import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  const context = await browser.newContext({ viewport: { width: 390, height: 900 } });
  await context.addInitScript(() => { delete window.IntersectionObserver; });
  await context.route('**/*', route => route.request().url().startsWith(origin) ? route.continue() : route.abort());
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(`${origin}/las-manecillas-del-recuerdo/fragmentos/`);
  assert.equal(await page.evaluate(() => 'IntersectionObserver' in window), false);
  for (const id of ['fragmento-1', 'fragmento-3', 'fragmento-2']) {
    await page.locator(`[data-fragment-link="${id}"]`).click();
    await page.waitForURL(url => url.hash === `#${id}`);
    assert.equal(await page.locator(`[data-fragment-link="${id}"]`).getAttribute('data-current'), 'true');
    assert(await page.locator(`#${id} .excerpt-field`).isVisible());
  }
  assert.deepEqual(errors, [], `Excepciones: ${errors.join(' | ')}`);
  await context.close();
  console.log('manecillas-intersectionobserver-fallback: OK');
} finally {
  await browser.close();
}
