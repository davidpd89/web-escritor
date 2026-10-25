import { chromium } from 'playwright';
import assert from 'node:assert/strict';

const base = process.env.BASE_URL || process.env.SITE_URL || 'http://127.0.0.1:8000';
const browser = await chromium.launch();
try {
  const page = await browser.newPage({ reducedMotion: 'reduce', viewport: { width: 1280, height: 800 } });
  await page.goto(new URL('/', base).href, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  const controls = page.locator('.primary-action, .form-submit, .header-buy');
  const count = await controls.count();
  assert.ok(count > 0, '/: no existen controles principales evaluables');
  for (let i = 0; i < count; i++) {
    const control = controls.nth(i);
    if (!await control.isVisible() || !await control.isEnabled()) continue;
    const name = (await control.innerText()).trim().slice(0, 60);
    for (const state of ['normal', 'hover', 'focus']) {
      if (state === 'hover') await control.hover();
      if (state === 'focus') await control.focus();
      if (state === 'normal') await page.mouse.move(0, 0);
      await control.evaluate(el => Promise.all(el.getAnimations().map(a => a.finished.catch(() => {}))));
      const contrast = await control.evaluate(el => {
        const rgb = v => { const m = v.match(/rgba?\(([^)]+)\)/); return m ? m[1].replaceAll(',', ' ').split(/\s+/).slice(0, 3).map(Number) : null; };
        const lum = a => a.map(v => { v /= 255; return v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; }).reduce((sum, v, i) => sum + v * [.2126, .7152, .0722][i], 0);
        const s = getComputedStyle(el), fg = rgb(s.color), bg = rgb(s.backgroundColor);
        if (!fg || !bg || bg.some(Number.isNaN)) return null;
        const a = lum(fg), b = lum(bg);
        return (Math.max(a, b) + .05) / (Math.min(a, b) + .05);
      });
      assert.ok(contrast !== null && contrast >= 4.5, `/: control '${name}' estado ${state}: contraste ${contrast?.toFixed(2) ?? 'indeterminado'}:1`);
    }
  }
} finally {
  await browser.close();
}
