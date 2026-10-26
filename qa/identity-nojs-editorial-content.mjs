import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.IDENTITY_BASE_URL || process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch();
try {
  for (const [route, expected] of [['/autor.html', 'David Porto Díaz'], ['/prensa.html', 'prensa']]) {
    const context = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 390, height: 844 } });
    try {
      const page = await context.newPage();
      const response = await page.goto(new URL(route, BASE).href, { waitUntil: 'load' });
      assert.equal(response?.status(), 200, `${route}: HTTP ${response?.status()}`);
      assert.equal(new URL(page.url()).pathname, route, `${route}: documento incorrecto`);
      const main = page.locator('main');
      assert.ok(await main.count(), `${route}: falta main`);
      const heading = main.locator('h1').first();
      assert.ok(await heading.isVisible(), `${route}: H1 invisible sin JavaScript`);
      const text = (await main.innerText()).trim();
      assert.ok(text.length > 300, `${route}: contenido editorial insuficiente (${text.length} caracteres)`);
      assert.ok(text.toLocaleLowerCase('es').includes(expected.toLocaleLowerCase('es')), `${route}: falta identidad editorial ${expected}`);
    } finally {
      await context.close();
    }
  }
} finally {
  await browser.close();
}
