import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  await page.addInitScript(() => {
    Object.defineProperty(window, 'sessionStorage', {
      configurable: true,
      get() { throw new DOMException('Blocked', 'SecurityError'); },
    });
  });
  await page.route('**/*', r => new URL(r.request().url()).origin === origin ? r.continue() : r.abort());
  await page.goto(origin + '/autor.html');
  await page.locator('.assistant-widget__launcher').waitFor();
  assert.equal(await page.locator('.assistant-widget__frame').count(), 0, 'Iframe creado sin interacción');
  await page.waitForTimeout(3900);
  assert.equal(await page.locator('.assistant-widget__hint').isVisible(), false, 'Pista visible con almacenamiento bloqueado');
  await page.locator('.assistant-widget__launcher').click();
  await page.locator('.assistant-widget__frame').waitFor();
  assert.equal(await page.locator('.assistant-widget__panel').isVisible(), true);
  assert.equal(await page.locator('.assistant-widget__frame').count(), 1);
} finally { await browser.close(); }
console.log('assistant-widget-storage-failure: OK');
