import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const cases = [
  { index: 0, hash: '#fragmento-1', title: 'El ritual del domingo' },
  { index: 1, hash: '#fragmento-2', title: 'El precio de una historia' },
  { index: 2, hash: '#fragmento-3', title: 'Las horas silenciosas' }
];
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  const context = await browser.newContext({ viewport: { width: 390, height: 900 }, reducedMotion: 'reduce' });
  await context.route('**/*', route => route.request().url().startsWith(origin) ? route.continue() : route.abort());
  const page = await context.newPage();
  for (const item of cases) {
    await page.goto(`${origin}/las-manecillas-del-recuerdo/`);
    const card = page.locator('.book-theme').nth(item.index);
    await card.click();
    await page.waitForURL(url => url.pathname.endsWith('/fragmentos/') && url.hash === item.hash);
    const heading = page.locator(`${item.hash} h2`);
    assert.equal((await heading.innerText()).trim(), item.title);
    assert(await page.locator(`${item.hash} .excerpt-field`).isVisible());
    assert.equal(await page.locator(`[data-fragment-link="${item.hash.slice(1)}"]`).getAttribute('data-current'), 'true');
  }
  await context.close();
  console.log('manecillas-theme-destination-journeys: OK');
} finally {
  await browser.close();
}
