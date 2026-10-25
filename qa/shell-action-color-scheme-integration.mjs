import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = (process.env.BASE_URL || process.env.TEST_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const browser = await chromium.launch();
try {
  for (const route of ['/', '/404.html']) {
    for (const scheme of ['light', 'dark']) {
      const page = await browser.newPage({ colorScheme: scheme, viewport: { width: 390, height: 844 } });
      try {
        const response = await page.goto(base + route, { waitUntil: 'load' });
        assert.equal(response.status(), 200, `${route} ${scheme}: HTTP`);
        await page.evaluate(() => document.fonts.ready);
        for (const selector of ['.site-header .header-buy', '.site-header .explore-trigger']) {
          const element = page.locator(selector);
          await element.waitFor({ state: 'visible' });
          const result = await element.evaluate(e => {
            const color = s => { const m = s.match(/rgba?\(([\d.]+)[, ]+\s*([\d.]+)[, ]+\s*([\d.]+)(?:[, /]+([\d.]+))?/); if (!m) throw Error(`Color no interpretable: ${s}`); return [Number(m[1]), Number(m[2]), Number(m[3]), m[4] === undefined ? 1 : Number(m[4])]; };
            const blend = (a, b) => a.slice(0, 3).map((v, i) => v * a[3] + b[i] * (1 - a[3]));
            const lum = c => c.map(v => { v /= 255; return v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; }).reduce((s, v, i) => s + v * [.2126, .7152, .0722][i], 0);
            const ancestors = []; for (let n = e; n; n = n.parentElement) ancestors.unshift(n);
            let bg = [255, 255, 255]; for (const n of ancestors) bg = blend(color(getComputedStyle(n).backgroundColor), bg);
            const fg = blend(color(getComputedStyle(e).color), bg);
            const a = lum(fg), b = lum(bg);
            return { ratio: (Math.max(a, b) + .05) / (Math.min(a, b) + .05), fg, bg };
          });
          assert.ok(result.ratio >= 4.5, `${route} ${scheme} ${selector}: contraste ${result.ratio.toFixed(2)}:1; texto/icono ${result.fg}, fondo ${result.bg}`);
        }
      } finally { await page.close(); }
    }
  }
} finally { await browser.close(); }
