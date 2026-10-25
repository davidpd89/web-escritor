import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN;
assert.ok(origin, 'QA_ORIGIN debe indicar el servidor HTTP local');
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
const routes = ['/', '/libros/', '/404.html'];
const widths = [320, 390, 768, 1280];
try {
  for (const width of widths) {
    const context = await browser.newContext({ viewport: { width, height: 850 }, reducedMotion: 'reduce' });
    try {
      const page = await context.newPage();
      for (const route of routes) {
        const response = await page.goto(new URL(route, origin).href, { waitUntil: 'domcontentloaded' });
        assert.equal(response?.status(), 200, `${route}: respuesta HTTP inesperada`);
        await page.locator('.site-header__inner').waitFor({ state: 'visible' });
        const controls = await page.locator('.site-header__inner :is(a,button)').evaluateAll(nodes => nodes.filter(el => {
          const s = getComputedStyle(el);
          return s.display !== 'none' && s.visibility === 'visible' && !el.disabled && el.getClientRects().length;
        }).map(el => {
          const r = el.getBoundingClientRect();
          return { name: el.getAttribute('aria-label') || el.textContent.trim() || el.className, x: r.x, y: r.y, width: r.width, height: r.height };
        }));
        assert.ok(controls.length >= 3, `${route} @${width}: faltan controles visibles de cabecera`);
        for (const c of controls) {
          assert.ok(c.width >= 43.5 && c.height >= 43.5, `${route} @${width}: ${c.name}, caja ${c.width}x${c.height}, mínimo 44x44`);
          assert.ok(c.x >= -1 && c.x + c.width <= width + 1, `${route} @${width}: ${c.name} fuera del viewport, x=${c.x}, ancho=${c.width}`);
        }
      }
      await page.close();
    } finally { await context.close(); }
  }
} finally { await browser.close(); }
