import { chromium } from 'playwright';
import assert from 'node:assert/strict';

const base = process.env.BASE_URL || process.env.SITE_URL || 'http://127.0.0.1:8000';
const browser = await chromium.launch();
try {
  const page = await browser.newPage();
  await page.goto(new URL('/', base).href, { waitUntil: 'load' });
  const pairs = await page.evaluate(() => {
    const root = getComputedStyle(document.documentElement);
    const values = [
      ['--color-text', '--surface-page'],
      ['--color-muted', '--surface-page'],
      ['--color-accent', '--surface-page'],
      ['--color-on-inverse', '--surface-inverse']
    ];
    const probe = document.createElement('span');
    probe.style.cssText = 'position:absolute;visibility:hidden;pointer-events:none';
    document.body.append(probe);
    const resolve = token => {
      probe.style.color = `var(${token})`;
      return getComputedStyle(probe).color;
    };
    const parse = v => {
      const match = v.match(/rgba?\(([^)]+)\)/);
      return match ? match[1].replaceAll(',', ' ').split(/\s+/).slice(0, 3).map(Number) : null;
    };
    const lum = rgb => rgb.map(x => { x /= 255; return x <= .04045 ? x / 12.92 : ((x + .055) / 1.055) ** 2.4; }).reduce((sum, x, i) => sum + x * [.2126, .7152, .0722][i], 0);
    const result = values.map(([foreground, background]) => {
      const a = parse(resolve(foreground)), b = parse(resolve(background));
      if (!a || !b || [...a, ...b].some(x => !Number.isFinite(x))) return { foreground, background, ratio: null };
      const x = lum(a), y = lum(b);
      return { foreground, background, ratio: (Math.max(x, y) + .05) / (Math.min(x, y) + .05) };
    });
    probe.remove();
    return result;
  });
  for (const pair of pairs) {
    assert.ok(pair.ratio !== null && pair.ratio >= 4.5, `/: tokens ${pair.foreground}/${pair.background}: contraste ${pair.ratio?.toFixed(2) ?? 'indeterminado'}:1, mínimo 4.5:1`);
  }
} finally {
  await browser.close();
}
