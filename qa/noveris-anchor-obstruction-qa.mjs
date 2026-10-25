import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
try {
  for (const width of [320, 390, 639, 640, 900, 1440]) {
    for (const modality of ['mouse', 'keyboard']) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: 'reduce' });
      await context.route('**/*', r => new URL(r.request().url()).origin === new URL(ORIGIN).origin ? r.continue() : r.abort());
      try {
        const page = await context.newPage();
        await page.goto(`${ORIGIN}/universo/noveris/`, { waitUntil: 'load' });
        const action = page.locator('.tool-hero a[href="#glosario"]');
        if (modality === 'mouse') await action.click();
        else { await action.focus(); await page.keyboard.press('Enter'); }
        await page.waitForTimeout(120);
        const result = await page.evaluate(() => {
          const target = document.getElementById('glosario').getBoundingClientRect();
          const blockers = ['.site-header', '.section-context'].map(s => document.querySelector(s)).filter(Boolean).filter(el => {
            const style = getComputedStyle(el);
            const r = el.getBoundingClientRect();
            return (style.position === 'sticky' || style.position === 'fixed') && r.top <= 1 && r.bottom > 0;
          }).map(el => el.getBoundingClientRect().bottom);
          return { hash: location.hash, top: target.top, bottom: target.bottom, blockedUntil: Math.max(0, ...blockers), viewport: innerHeight };
        });
        assert.equal(result.hash, '#glosario', `${width}/${modality}: hash incorrecto`);
        assert.ok(result.top >= result.blockedUntil - 2, `${width}/${modality}: sección oculta bajo navegación (${JSON.stringify(result)})`);
        assert.ok(result.top < result.viewport, `${width}/${modality}: sección fuera del viewport`);
        assert.ok(result.bottom > result.blockedUntil, `${width}/${modality}: sección invisible`);
      } finally {
        await context.close();
      }
    }
  }
} finally {
  await browser.close();
}
console.log('noveris-anchor-obstruction: PASS');