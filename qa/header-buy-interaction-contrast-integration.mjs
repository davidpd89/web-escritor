import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = (process.env.BASE_URL || process.env.TEST_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const browser = await chromium.launch({ headless: true });
const routes = ['/', '/libros/', '/404.html'];
const rgb = s => { const m = s.match(/^rgba?\((\d+)[, ]+\s*(\d+)[, ]+\s*(\d+)/); assert.ok(m, `Color no RGB: ${s}`); return m.slice(1, 4).map(Number); };
const luminance = c => c.map(x => { x /= 255; return x <= .04045 ? x / 12.92 : ((x + .055) / 1.055) ** 2.4; }).reduce((s, v, i) => s + v * [.2126, .7152, .0722][i], 0);
const ratio = (a, b) => { const x = luminance(rgb(a)), y = luminance(rgb(b)); return (Math.max(x, y) + .05) / (Math.min(x, y) + .05); };
try {
  for (const route of routes) {
    const page = await browser.newPage({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' });
    try {
      const response = await page.goto(base + route, { waitUntil: 'load' });
      assert.equal(response.status(), 200, `${route}: HTTP inesperado`);
      await page.evaluate(() => document.fonts.ready);
      const buy = page.locator('.site-header .header-buy');
      await buy.waitFor({ state: 'visible' });
      for (const state of ['normal', 'hover', 'focus']) {
        if (state === 'hover') await buy.hover();
        if (state === 'focus') await buy.focus();
        if (state !== 'normal') await page.waitForFunction(() => { const e = document.querySelector('.site-header .header-buy'); return e && getComputedStyle(e).transitionDuration.split(',').every(v => parseFloat(v) === 0); });
        const colors = await buy.evaluate(e => { const s = getComputedStyle(e); return { color: s.color, background: s.backgroundColor, text: e.textContent.trim() }; });
        assert.ok(colors.background !== 'rgba(0, 0, 0, 0)', `${route} ${state}: fondo transparente no evaluable`);
        const value = ratio(colors.color, colors.background);
        assert.ok(value >= 4.5, `${route} ${state}: Comprar (${colors.text}) contraste ${value.toFixed(2)}:1; texto ${colors.color}, fondo ${colors.background}`);
      }
    } finally { await page.close(); }
  }
} finally { await browser.close(); }
