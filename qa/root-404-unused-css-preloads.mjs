import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = process.env.BASE_URL || process.env.TEST_BASE_URL || 'http://127.0.0.1:8000';
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  const response = await page.goto(new URL('/404.html', base).href, { waitUntil: 'load' });
  assert.equal(response.status(), 200, '/404.html: respuesta HTTP inesperada');
  const result = await page.evaluate(async () => {
    const preloads = [...document.querySelectorAll('link[rel="preload"][as="style"]')];
    await Promise.all(preloads.map(link => {
      const href = link.href;
      const sheet = [...document.styleSheets].find(s => s.href === href);
      if (sheet) return Promise.resolve();
      return Promise.resolve();
    }));
    const resources = performance.getEntriesByType('resource');
    return preloads.map(link => ({
      url: link.href,
      requested: resources.some(r => r.name === link.href),
      directConsumer: [...document.querySelectorAll('link[rel="stylesheet"]')].some(s => s.href === link.href)
    }));
  });
  assert.ok(result.length, '/404.html: no se encontraron precargas CSS; revisar si el contrato sigue siendo aplicable');
  for (const item of result) {
    assert.ok(item.requested, `/404.html: precarga sin petición observable: ${item.url}`);
    assert.ok(item.directConsumer, `/404.html: precarga CSS sin consumidor directo: ${item.url}`);
  }
  console.log('PASS 404 CSS preload consumption');
} finally {
  await browser.close();
}