import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch();
try {
  for (const width of [390, 1280]) {
    const context = await browser.newContext({ javaScriptEnabled: false, viewport: { width, height: 844 } });
    try {
      const page = await context.newPage();
      const response = await page.goto(new URL('/offline.html', BASE).href, { waitUntil: 'load' });
      assert.equal(response?.status(), 200, `/offline.html ${width}px: HTTP ${response?.status()}`);
      const heading = page.locator('main h1');
      assert.ok(await heading.isVisible(), `/offline.html ${width}px: título invisible`);
      assert.match(await heading.innerText(), /red/i, `/offline.html ${width}px: mensaje principal incorrecto`);
      const text = await page.locator('main').innerText();
      assert.match(text, /reintentar/i, `/offline.html ${width}px: falta instrucción de recuperación`);
      assert.match(text, /historial/i, `/offline.html ${width}px: falta alternativa de historial`);
      assert.equal(await page.locator('.actions button:visible').count(), 0, `/offline.html ${width}px: botones inoperativos visibles sin JavaScript`);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      assert.ok(overflow <= 1, `/offline.html ${width}px: desbordamiento horizontal ${overflow}px`);
    } finally {
      await context.close();
    }
  }
} finally {
  await browser.close();
}
