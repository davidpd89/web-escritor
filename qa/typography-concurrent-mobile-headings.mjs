import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || process.env.BASE_URL || 'http://127.0.0.1:8000';
const routes = ['/', '/autor.html', '/libros/', '/recomendaciones/', '/editoriales/'];
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
const context = await browser.newContext({ viewport: { width: 320, height: 700 }, deviceScaleFactor: 1, serviceWorkers: 'block' });
try {
  await Promise.all(routes.map(async route => {
    const page = await context.newPage();
    try {
      const response = await page.goto(new URL(route, BASE).href, { waitUntil: 'load', timeout: 30000 });
      assert.equal(response?.status(), 200, `${route}: HTTP ${response?.status()}`);
      await page.evaluate(() => document.fonts.ready);
      const result = await page.evaluate(() => {
        const h = document.querySelector('h1');
        if (!h) return null;
        const rect = h.getBoundingClientRect();
        const style = getComputedStyle(h);
        return { text: h.innerText.trim(), x: rect.x, right: rect.right, width: rect.width, height: rect.height, clientHeight: h.clientHeight, scrollHeight: h.scrollHeight, overflowY: style.overflowY, fontSize: style.fontSize, documentWidth: document.documentElement.scrollWidth };
      });
      assert(result?.text, `${route}: H1 vacío o ausente`);
      assert(result.width > 0 && result.height > 0, `${route}: H1 sin caja visible`);
      assert(result.x >= -2 && result.right <= 322, `${route}: H1 fuera del viewport móvil: ${JSON.stringify(result)}`);
      assert(result.documentWidth <= 322, `${route}: desbordamiento horizontal (${result.documentWidth}px)`);
      if (['hidden', 'clip'].includes(result.overflowY)) assert(result.scrollHeight <= result.clientHeight + 2, `${route}: H1 recortado verticalmente`);
    } finally {
      await page.close();
    }
  }));
  console.log('OK: encabezados móviles bajo carga concurrente');
} finally {
  await browser.close();
}