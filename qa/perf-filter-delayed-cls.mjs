import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const cases = [
  { route: '/recomendaciones/', selector: 'input[data-facet="grupo"]:not([disabled])', action: 'check' },
  { route: '/convocatorias-escritores/', selector: '[data-radar-search]', action: 'fill' }
];
const browser = await chromium.launch({ headless: true });
const failures = [];
try {
  for (const test of cases) {
    for (const width of [390, 1440]) {
      const page = await browser.newPage({ viewport: { width, height: 900 }, reducedMotion: 'reduce' });
      await page.route('**/*', r => {
        const u = new URL(r.request().url());
        return u.origin === new URL(BASE).origin || ['data:', 'blob:'].includes(u.protocol) ? r.continue() : r.abort();
      });
      await page.addInitScript(() => {
        window.__qaLateShifts = [];
        new PerformanceObserver(list => {
          for (const e of list.getEntries()) if (!e.hadRecentInput) window.__qaLateShifts.push({ value: e.value, time: e.startTime });
        }).observe({ type: 'layout-shift', buffered: true });
      });
      try {
        await page.goto(BASE + test.route, { waitUntil: 'load' });
        const control = page.locator(test.selector).first();
        await control.waitFor({ state: 'visible' });
        await page.waitForTimeout(700);
        const before = await page.evaluate(() => performance.now());
        if (test.action === 'check') await control.check();
        else await control.fill('convocatoria inexistente qa');
        await page.waitForTimeout(1200);
        const shift = await page.evaluate(t => window.__qaLateShifts.filter(x => x.time >= t).reduce((sum, x) => sum + x.value, 0), before);
        if (shift > 0.1) failures.push(`${test.route} ${width}px: CLS tardío ${shift.toFixed(4)}`);
      } finally {
        await page.close();
      }
    }
  }
} finally {
  await browser.close();
}
assert.deepEqual(failures, [], failures.join('\n'));
console.log('PASS CLS diferido tras filtros');
