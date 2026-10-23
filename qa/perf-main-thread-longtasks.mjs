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
const routes = [...groups.values()].flatMap(rows => rows.sort((a,b) => a.url.localeCompare(b.url)).slice(0, 2)).map(x => x.url);
assert(routes.length >= 8, 'Muestra insuficiente');
const browser = await chromium.launch({ headless: true });
const failures = [];
try {
  for (const route of routes) {
    const page = await browser.newPage({ viewport: { width: 390, height: 900 }, reducedMotion: 'reduce' });
    await page.route('**/*', r => {
      const u = new URL(r.request().url());
      return u.origin === new URL(BASE).origin || ['data:', 'blob:'].includes(u.protocol) ? r.continue() : r.abort();
    });
    await page.addInitScript(() => {
      window.__qaTasks = [];
      new PerformanceObserver(list => {
        for (const e of list.getEntries()) window.__qaTasks.push(e.duration);
      }).observe({ type: 'longtask', buffered: true });
    });
    try {
      await page.goto(BASE + route, { waitUntil: 'load' });
      await page.waitForTimeout(800);
      const report = await page.evaluate(() => ({
        maximum: Math.max(0, ...window.__qaTasks),
        blocking: window.__qaTasks.reduce((sum, duration) => sum + Math.max(0, duration - 50), 0),
        count: window.__qaTasks.length
      }));
      if (report.maximum > 200 || report.blocking > 500) failures.push(`${route}: ${JSON.stringify(report)}`);
    } finally {
      await page.close();
    }
  }
} finally {
  await browser.close();
}
assert.deepEqual(failures, [], failures.join('\n'));
console.log(`PASS longtasks en ${routes.length} rutas`);
