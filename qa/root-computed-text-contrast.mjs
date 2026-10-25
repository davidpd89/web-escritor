import { chromium } from 'playwright';
import assert from 'node:assert/strict';

const base = process.env.BASE_URL || process.env.SITE_URL || 'http://127.0.0.1:8000';
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  await page.goto(new URL('/', base).href, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  await page.locator('body').waitFor({ state: 'visible' });
  const results = await page.evaluate(() => {
    const parse = value => {
      const match = value.match(/rgba?\(([^)]+)\)/);
      if (!match) return null;
      const parts = match[1].replaceAll(',', ' ').replace('/', ' ').split(/\s+/).filter(Boolean).map(Number);
      return parts.length >= 3 && parts.every(Number.isFinite) ? [parts[0], parts[1], parts[2], parts[3] ?? 1] : null;
    };
    const luminance = rgb => {
      const c = rgb.slice(0, 3).map(v => { const n = v / 255; return n <= .04045 ? n / 12.92 : ((n + .055) / 1.055) ** 2.4; });
      return c[0] * .2126 + c[1] * .7152 + c[2] * .0722;
    };
    const ratio = (a, b) => { const x = luminance(a), y = luminance(b); return (Math.max(x, y) + .05) / (Math.min(x, y) + .05); };
    const blend = (fg, bg) => fg.slice(0, 3).map((v, i) => v * fg[3] + bg[i] * (1 - fg[3]));
    const background = element => {
      const layers = [];
      for (let node = element; node; node = node.parentElement) {
        const color = parse(getComputedStyle(node).backgroundColor);
        if (color && color[3] > 0) layers.push(color);
      }
      let result = [255, 255, 255];
      for (const layer of layers.reverse()) result = blend(layer, result);
      return result;
    };
    return [...document.querySelectorAll('main p, main li, .site-header button, .site-header a, footer a')].filter(el => {
      const s = getComputedStyle(el), r = el.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && s.visibility === 'visible' && s.display !== 'none' && s.opacity !== '0' && el.textContent.trim() && s.backgroundImage === 'none';
    }).slice(0, 100).map(el => {
      const s = getComputedStyle(el), fg = parse(s.color);
      const bg = background(el);
      return { element: el.tagName.toLowerCase(), text: el.textContent.trim().slice(0, 55), ratio: fg ? ratio(blend(fg, bg), bg) : null };
    });
  });
  assert.ok(results.length > 0, '/: no se encontraron textos evaluables');
  for (const result of results) {
    assert.ok(result.ratio !== null && result.ratio >= 4.5, `/: contraste insuficiente en ${result.element} '${result.text}': ${result.ratio?.toFixed(2) ?? 'indeterminado'}:1`);
  }
} finally {
  await browser.close();
}
