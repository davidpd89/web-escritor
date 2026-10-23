import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright';

const BASE = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const registry = JSON.parse(fs.readFileSync('data/content-registry.json', 'utf8'));
const groups = new Map();
for (const x of registry.entries) {
  if ((x.status ?? registry.defaults.status) !== 'public' || !String(x.sourceFile || '').endsWith('.html')) continue;
  const key = x.territory || x.type || 'other';
  if (!groups.has(key)) groups.set(key, []);
  groups.get(key).push(x);
}
const cases = [...groups.values()].flatMap(rows => rows.sort((a,b) => a.url.localeCompare(b.url)).slice(0, 2));
assert(cases.length >= 8, 'Cobertura de familias insuficiente');
const browser = await chromium.launch({ headless: true });
const failures = [];
try {
  for (const x of cases) {
    for (const width of [390, 1440]) {
      const page = await browser.newPage({ viewport: { width, height: 900 }, reducedMotion: 'reduce' });
      await page.route('**/*', r => {
        const u = new URL(r.request().url());
        return u.origin === new URL(BASE).origin || ['data:', 'blob:'].includes(u.protocol) ? r.continue() : r.abort();
      });
      await page.addInitScript(() => {
        window.__qaShift = 0;
        new PerformanceObserver(list => {
          for (const e of list.getEntries()) if (!e.hadRecentInput) window.__qaShift += e.value;
        }).observe({ type: 'layout-shift', buffered: true });
      });
      try {
        const response = await page.goto(BASE + x.url, { waitUntil: 'load', timeout: 30000 });
        assert.equal(response.status(), 200, x.url);
        await page.waitForTimeout(1000);
        const value = await page.evaluate(() => window.__qaShift);
        if (value > 0.1) failures.push(`${x.url} ${width}px CLS=${value.toFixed(4)}`);
      } finally {
        await page.close();
      }
    }
  }
} finally {
  await browser.close();
}
assert.deepEqual(failures, [], failures.join('\n'));
console.log(`PASS CLS: ${cases.length} rutas, dos viewports`);
