import { chromium } from 'playwright';
import assert from 'node:assert/strict';

const base = process.env.BASE_URL || process.env.SITE_URL || 'http://127.0.0.1:8000';
const browser = await chromium.launch();
try {
  const results = {};
  for (const scheme of ['light', 'dark']) {
    const context = await browser.newContext({ colorScheme: scheme, reducedMotion: 'reduce' });
    try {
      await context.route(/https?:\/\//, route => {
        const url = new URL(route.request().url());
        if (url.origin !== new URL(base).origin) return route.abort();
        return route.continue();
      });
      const page = await context.newPage();
      const css = new Set();
      page.on('request', request => {
        if (request.resourceType() === 'stylesheet') css.add(new URL(request.url()).pathname);
      });
      await page.goto(new URL('/', base).href, { waitUntil: 'load' });
      await page.evaluate(() => document.fonts.ready);
      const colors = await page.evaluate(() => {
        const rgb = v => { const m = v.match(/rgba?\(([^)]+)\)/); return m ? m[1].replaceAll(',', ' ').split(/\s+/).slice(0, 3).map(Number) : null; };
        const lum = a => a.map(v => { v /= 255; return v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; }).reduce((sum, v, i) => sum + v * [.2126, .7152, .0722][i], 0);
        return ['html', 'body'].map(selector => {
          const s = getComputedStyle(document.querySelector(selector));
          const fg = rgb(s.color), bg = rgb(s.backgroundColor);
          if (!fg || !bg) return { selector, ratio: null };
          const a = lum(fg), b = lum(bg);
          return { selector, ratio: (Math.max(a, b) + .05) / (Math.min(a, b) + .05) };
        });
      });
      results[scheme] = { css: [...css].sort(), colors };
      for (const item of colors) {
        assert.ok(item.ratio !== null && item.ratio >= 4.5, `/: modo ${scheme}, ${item.selector}: contraste ${item.ratio?.toFixed(2) ?? 'indeterminado'}:1`);
      }
    } finally {
      await context.close();
    }
  }
  assert.deepEqual(results.dark.css, results.light.css, `/: modo oscuro introduce o elimina recursos CSS: dark=${results.dark.css.join(',')} light=${results.light.css.join(',')}`);
} finally {
  await browser.close();
}
