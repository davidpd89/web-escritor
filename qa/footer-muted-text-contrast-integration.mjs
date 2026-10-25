import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = (process.env.BASE_URL || process.env.TEST_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const browser = await chromium.launch();
try {
  for (const route of ['/', '/libros/', '/404.html']) {
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
    try {
      const response = await page.goto(base + route, { waitUntil: 'load' });
      assert.equal(response.status(), 200, `${route}: HTTP`);
      await page.evaluate(() => document.fonts.ready);
      const results = await page.locator('.site-footer p').evaluateAll(nodes => {
        const parse = s => { const m = s.match(/rgba?\(([\d.]+)[, ]+\s*([\d.]+)[, ]+\s*([\d.]+)(?:[, /]+([\d.]+))?/); if (!m) throw Error(`Color inesperado ${s}`); return [Number(m[1]), Number(m[2]), Number(m[3]), m[4] === undefined ? 1 : Number(m[4])]; };
        const mix = (a, b) => a.slice(0, 3).map((v, i) => v * a[3] + b[i] * (1 - a[3]));
        const lum = c => c.map(x => { x /= 255; return x <= .04045 ? x / 12.92 : ((x + .055) / 1.055) ** 2.4; }).reduce((s, x, i) => s + x * [.2126, .7152, .0722][i], 0);
        return nodes.filter(e => e.getClientRects().length && e.textContent.trim()).map(e => {
          const ancestors = []; for (let n = e; n; n = n.parentElement) ancestors.unshift(n);
          let bg = [255, 255, 255]; for (const n of ancestors) bg = mix(parse(getComputedStyle(n).backgroundColor), bg);
          const fg = mix(parse(getComputedStyle(e).color), bg);
          const a = lum(fg), b = lum(bg);
          return { text: e.textContent.trim().slice(0, 70), ratio: (Math.max(a, b) + .05) / (Math.min(a, b) + .05), fg, bg };
        });
      });
      assert.ok(results.length, `${route}: no se encontraron párrafos visibles en el pie`);
      for (const r of results) assert.ok(r.ratio >= 4.5, `${route}: pie «${r.text}», contraste ${r.ratio.toFixed(2)}:1; texto ${r.fg}, fondo ${r.bg}`);
    } finally { await page.close(); }
  }
} finally { await browser.close(); }
