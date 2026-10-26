import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const ROUTE = '/donde-empieza-la-jaula/';
const MAX_TOTAL = 1024 * 1024;
const MAX_SINGLE = 512 * 1024;
const browser = await chromium.launch({ headless: true });

try {
  for (const width of [390, 1440]) {
    const context = await browser.newContext({ viewport: { width, height: 900 } });
    const page = await context.newPage();
    const resources = [];

    page.on('response', async response => {
      const url = new URL(response.url());
      if (url.origin !== ORIGIN || !/\.(css|js)$/i.test(url.pathname)) return;
      resources.push(response);
    });

    const navigation = await page.goto(`${ORIGIN}${ROUTE}`, { waitUntil: 'load' });
    assert.equal(navigation?.status(), 200, `${ROUTE} ${width}px: documento inaccesible`);

    const measured = [];
    for (const response of resources) {
      const url = new URL(response.url());
      assert.ok(response.ok(), `${ROUTE} ${width}px: ${url.pathname} HTTP ${response.status()}`);
      const sizes = await response.request().sizes();
      measured.push({ path: url.pathname, bytes: sizes.responseBodySize + sizes.responseHeadersSize });
    }

    assert.ok(measured.length > 0, `${ROUTE} ${width}px: no se han medido recursos`);
    const total = measured.reduce((sum, item) => sum + item.bytes, 0);
    assert.ok(total <= MAX_TOTAL, `${ROUTE} ${width}px: CSS+JS ${total} bytes, máximo ${MAX_TOTAL}`);
    for (const item of measured) {
      assert.ok(item.bytes <= MAX_SINGLE, `${ROUTE} ${width}px: ${item.path} ocupa ${item.bytes} bytes, máximo ${MAX_SINGLE}`);
    }
    console.log(`${ROUTE} ${width}px: ${measured.length} recursos, ${total} bytes`);
    await context.close();
  }
  console.log('OK jaula initial resource budget');
} finally {
  await browser.close();
}
