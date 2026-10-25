import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:8000';
const browser = await chromium.launch({ headless: true });
const candidates = ['hero-tinta-poster.webp', 'manecillas-del-recuerdo-3d-transparent.webp'];

try {
  for (const returning of [false, true]) {
    const context = await browser.newContext({ serviceWorkers: 'block' });
    await context.route(/^https?:\/\//, route => {
      if (new URL(route.request().url()).origin !== new URL(origin).origin) return route.abort();
      return route.continue();
    });
    await context.addInitScript(value => {
      if (value) sessionStorage.setItem('dp-intro-seen', '1');
      else sessionStorage.removeItem('dp-intro-seen');
    }, returning);
    const page = await context.newPage();
    const requests = [];
    page.on('request', request => {
      if (candidates.some(name => new URL(request.url()).pathname.endsWith(name))) requests.push(request.url());
    });
    try {
      const response = await page.goto(origin + '/', { waitUntil: 'load' });
      assert.equal(response.status(), 200, '/: HTTP inesperado');
      const preloads = await page.locator('link[rel="preload"][as="image"]').evaluateAll(nodes => nodes.map(n => n.href));
      const expected = returning ? candidates[1] : candidates[0];
      const unwanted = returning ? candidates[0] : candidates[1];
      assert.equal(preloads.filter(url => url.includes(expected)).length, 1, `/: estado recurrente=${returning}: precarga LCP esperada ${expected}`);
      assert.equal(preloads.filter(url => url.includes(unwanted)).length, 0, `/: estado recurrente=${returning}: precarga LCP innecesaria ${unwanted}`);
      assert.ok(requests.some(url => url.includes(expected)), `/: estado recurrente=${returning}: no se solicitó ${expected}`);
      assert.ok(!requests.some(url => url.includes(unwanted)), `/: estado recurrente=${returning}: descarga competidora ${unwanted}`);
    } finally {
      await context.close();
    }
  }
} finally {
  await browser.close();
}
