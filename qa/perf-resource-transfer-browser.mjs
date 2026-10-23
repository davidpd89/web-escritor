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
    try {
      const response = await page.goto(BASE + route, { waitUntil: 'load' });
      assert.equal(response.status(), 200, route);
      await page.waitForTimeout(500);
      const metrics = await page.evaluate(() => {
        const resources = performance.getEntriesByType('resource').filter(r => new URL(r.name).origin === location.origin);
        const navigation = performance.getEntriesByType('navigation')[0];
        const bytes = resources.reduce((sum, r) => sum + (r.encodedBodySize || r.decodedBodySize || 0), 0) + (navigation?.encodedBodySize || navigation?.decodedBodySize || 0);
        return { bytes, requests: resources.length + 1, measuredResources: resources.filter(r => (r.encodedBodySize || r.decodedBodySize) > 0).length };
      });
      assert(metrics.measuredResources > 0, `${route}: Resource Timing sin tamaños observables`);
      console.log(`${route}: ${JSON.stringify(metrics)}`);
      if (metrics.bytes > 3 * 1024 * 1024 || metrics.requests > 100) failures.push(`${route}: ${JSON.stringify(metrics)}`);
    } finally {
      await page.close();
    }
  }
} finally {
  await browser.close();
}
assert.deepEqual(failures, [], failures.join('\n'));
console.log(`PASS transferencia inicial en ${routes.length} rutas`);
