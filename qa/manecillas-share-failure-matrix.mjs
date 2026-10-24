import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  for (const mode of ['abort', 'clipboard', 'reject']) {
    const context = await browser.newContext();
    await context.route('**/*', route => route.request().url().startsWith(origin) ? route.continue() : route.abort());
    await context.addInitScript(mode => {
      window.__copied = null;
      Object.defineProperty(navigator, 'share', { configurable: true, value: async () => {
        const error = new Error('Simulated native-share failure');
        error.name = mode === 'abort' ? 'AbortError' : 'NotAllowedError';
        throw error;
      }});
      Object.defineProperty(navigator, 'clipboard', { configurable: true, value: {
        writeText: async value => {
          if (mode === 'reject') throw new Error('Clipboard denied');
          window.__copied = value;
        }
      }});
    }, mode);
    const page = await context.newPage();
    await page.goto(`${origin}/las-manecillas-del-recuerdo/`);
    await page.locator('[data-book-share]').click();
    const result = await page.evaluate(() => ({ copied: window.__copied, status: document.querySelector('#book-share-status').textContent.trim() }));
    if (mode === 'abort') {
      assert.equal(result.copied, null);
      assert.equal(result.status, '');
    } else if (mode === 'clipboard') {
      assert.equal(result.copied, 'https://davidportodiaz.com/las-manecillas-del-recuerdo/');
      assert.match(result.status, /Enlace copiado/);
    } else {
      assert.equal(result.copied, null);
      assert.match(result.status, /No se pudo copiar/);
    }
    await context.close();
  }
  console.log('manecillas-share-failure-matrix: OK');
} finally {
  await browser.close();
}
