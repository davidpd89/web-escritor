import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.IDENTITY_BASE_URL || process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch();
try {
  for (const route of ['/autor.html', '/prensa.html']) {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
    try {
      await context.route('**/assets/v1-shell.js*', request => request.abort('failed'));
      const page = await context.newPage();
      const response = await page.goto(new URL(route, BASE).href, { waitUntil: 'load' });
      assert.equal(response?.status(), 200, `${route}: HTTP ${response?.status()}`);
      assert.equal(new URL(page.url()).pathname, route, `${route}: documento incorrecto`);
      const heading = page.locator('main h1').first();
      assert.ok(await heading.isVisible(), `${route}: H1 desaparece al fallar v1-shell.js`);
      const text = (await page.locator('main').innerText()).trim();
      assert.ok(text.length > 300, `${route}: contenido perdido tras fallo de v1-shell.js (${text.length} caracteres)`);
      assert.ok(await page.locator('footer a[href="/autor.html"]').isVisible(), `${route}: navegación de pie inaccesible`);
    } finally {
      await context.close();
    }
  }
} finally {
  await browser.close();
}
