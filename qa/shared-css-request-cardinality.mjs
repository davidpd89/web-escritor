import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:8000';
const css = readFileSync('assets/v1-shell.css', 'utf8');
const imports = [...css.matchAll(/@import\s+url\(['"]?([^)'"\s]+)['"]?\)/g)].map(m => new URL(m[1], origin).pathname);
assert.ok(imports.length >= 9, 'v1-shell.css: no se ha descubierto la cadena CSS compartida');
const browser = await chromium.launch({ headless: true });

try {
  for (const route of ['/', '/404.html']) {
    const context = await browser.newContext({ serviceWorkers: 'block' });
    await context.route(/^https?:\/\//, request => new URL(request.request().url()).origin === new URL(origin).origin ? request.continue() : request.abort());
    const page = await context.newPage();
    const counts = new Map();
    page.on('request', request => {
      const pathname = new URL(request.url()).pathname;
      if (imports.includes(pathname)) counts.set(pathname, (counts.get(pathname) || 0) + 1);
    });
    try {
      const response = await page.goto(new URL(route, origin).href, { waitUntil: 'load' });
      assert.equal(response.status(), 200, `${route}: respuesta HTTP`);
      await page.evaluate(() => document.fonts.ready);
      for (const pathname of imports) {
        assert.equal(counts.get(pathname), 1, `${route}: ${pathname} produjo ${counts.get(pathname) || 0} solicitudes, esperado 1`);
      }
    } finally {
      await context.close();
    }
  }
} finally {
  await browser.close();
}
