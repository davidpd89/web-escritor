import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const route = '/convocatorias-escritores/';
const browser = await chromium.launch();
try {
  for (const width of [320, 390, 768, 1440]) {
    const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    try {
      await page.addInitScript(() => {
        window.__layoutShifts = [];
        new PerformanceObserver(list => {
          for (const entry of list.getEntries()) if (!entry.hadRecentInput) window.__layoutShifts.push({ value: entry.value, time: entry.startTime });
        }).observe({ type: 'layout-shift', buffered: true });
      });
      const response = await page.goto(origin + route, { waitUntil: 'load' });
      assert.equal(response?.status(), 200, `${route} ${width}px: HTTP incorrecto`);
      await page.evaluate(async () => {
        await document.fonts.ready;
        await Promise.all([...document.querySelectorAll('link[rel="stylesheet"]')].map(link => link.sheet ? Promise.resolve() : new Promise(resolve => { link.addEventListener('load', resolve, { once: true }); link.addEventListener('error', resolve, { once: true }); })));
      });
      const shifts = await page.evaluate(() => window.__layoutShifts);
      let maximum = 0, session = 0, last = -Infinity, first = -Infinity;
      for (const entry of shifts) {
        if (entry.time - last > 1000 || entry.time - first > 5000) { session = 0; first = entry.time; }
        session += entry.value;
        maximum = Math.max(maximum, session);
        last = entry.time;
      }
      assert.ok(maximum <= 0.05, `${route} ${width}px: CLS ${maximum.toFixed(4)} supera 0,05`);
      for (const selector of ['[data-radar-search]', '[data-radar-type]', '[data-radar-genre]', 'select#radar-kind[data-radar-kind]', '[data-radar-calendar]', '[data-radar-clear]']) {
        const control = page.locator(selector);
        assert.equal(await control.count(), 1, `${route} ${width}px: falta ${selector}`);
        await control.focus();
        const geometry = await control.evaluate(el => {
          const r = el.getBoundingClientRect();
          const style = getComputedStyle(el);
          return { left: r.left, right: r.right, top: r.top, bottom: r.bottom, width: r.width, height: r.height, visibility: style.visibility, active: document.activeElement === el, viewportWidth: innerWidth, viewportHeight: innerHeight };
        });
        assert.ok(geometry.active, `${route} ${width}px: ${selector} no conserva el foco`);
        assert.ok(geometry.width > 0 && geometry.height > 0 && geometry.visibility === 'visible', `${route} ${width}px: ${selector} sin geometría visible`);
        assert.ok(geometry.left >= -1 && geometry.right <= geometry.viewportWidth + 1 && geometry.top >= -1 && geometry.bottom <= geometry.viewportHeight + 1, `${route} ${width}px: ${selector} fuera de viewport: ${JSON.stringify(geometry)}`);
      }
    } finally {
      await context.close();
    }
  }
} finally {
  await browser.close();
}