import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const ROUTES = ['/recomendaciones/', '/recomendaciones/libros/coraline/', '/recomendaciones/autores/neil-gaiman/', '/editoriales/', '/cuaderno/'];
const browser = await chromium.launch({ headless: true });
try {
  for (const width of [320, 390, 768, 1024, 1440]) {
    const context = await browser.newContext({ viewport: { width, height: 900 } });
    try {
      const page = await context.newPage();
      for (const route of ROUTES) {
        const response = await page.goto(new URL(route, BASE).href, { waitUntil: 'load' });
        assert.equal(response?.status(), 200, `${route} @ ${width}: HTTP incorrecto`);
        await page.evaluate(() => document.fonts.ready);
        assert.equal(await page.locator('main').count(), 1, `${route} @ ${width}: número de regiones main incorrecto`);
        const h1 = page.locator('main h1');
        assert.equal(await h1.count(), 1, `${route} @ ${width}: debe existir un H1 principal`);
        assert.ok(await h1.isVisible(), `${route} @ ${width}: H1 oculto`);
        assert.ok((await h1.innerText()).trim().length > 0, `${route} @ ${width}: H1 vacío`);
        const state = await h1.evaluate(el => {
          const r = el.getBoundingClientRect();
          const s = getComputedStyle(el);
          return { left: r.left, right: r.right, width: r.width, fontSize: parseFloat(s.fontSize), lineHeight: s.lineHeight, visibility: s.visibility };
        });
        assert.ok(state.left >= -1 && state.right <= width + 1, `${route} @ ${width}: H1 desbordado ${JSON.stringify(state)}`);
        assert.ok(state.fontSize >= 16, `${route} @ ${width}: H1 demasiado pequeño: ${state.fontSize}px`);
        assert.notEqual(state.visibility, 'hidden', `${route} @ ${width}: H1 invisible`);
      }
    } finally { await context.close(); }
  }
} finally { await browser.close(); }
