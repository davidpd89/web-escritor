import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = (process.env.BASE_URL || process.env.TEST_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const browser = await chromium.launch();
const routes = ['/', '/404.html'];
try {
  for (const route of routes) {
    const page = await browser.newPage({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' });
    try {
      const response = await page.goto(base + route, { waitUntil: 'load' });
      assert.equal(response.status(), 200, `${route}: respuesta HTTP`);
      await page.evaluate(() => document.fonts.ready);
      await page.locator('[data-explore-open]').click();
      await page.locator('[data-explore-dialog][open]').waitFor({ state: 'visible' });
      await page.waitForFunction(() => { const e = document.querySelector('[data-explore-dialog]'); return e && Math.abs(e.getBoundingClientRect().right - innerWidth) < 2; });
      const results = await page.locator('.explore-row__index, .explore-row__body small').evaluateAll(elements => {
        const rgba = value => { const m = value.match(/rgba?\(([\d.]+)[, ]+\s*([\d.]+)[, ]+\s*([\d.]+)(?:[, /]+([\d.]+))?/); if (!m) throw Error(`Color inesperado: ${value}`); return [Number(m[1]), Number(m[2]), Number(m[3]), m[4] === undefined ? 1 : Number(m[4])]; };
        const blend = (top, bottom) => top.slice(0, 3).map((x, i) => x * top[3] + bottom[i] * (1 - top[3]));
        const lum = c => c.map(v => { v /= 255; return v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; }).reduce((s, v, i) => s + v * [.2126, .7152, .0722][i], 0);
        return elements.filter(e => e.getClientRects().length).map(e => {
          let background = [255, 255, 255];
          const ancestors = []; for (let p = e; p; p = p.parentElement) ancestors.unshift(p);
          for (const p of ancestors) background = blend(rgba(getComputedStyle(p).backgroundColor), background);
          const foreground = blend(rgba(getComputedStyle(e).color), background);
          const a = lum(foreground), b = lum(background);
          return { text: e.textContent.trim(), ratio: (Math.max(a, b) + .05) / (Math.min(a, b) + .05), foreground, background };
        });
      });
      assert.ok(results.length > 0, `${route}: sin textos secundarios visibles`);
      for (const r of results) assert.ok(r.ratio >= 4.5, `${route}: «${r.text}» contraste ${r.ratio.toFixed(2)}:1; texto ${r.foreground}, fondo ${r.background}`);
    } finally { await page.close(); }
  }
} finally { await browser.close(); }
