import assert from 'node:assert/strict';
import {chromium, firefox, webkit} from 'playwright';
const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const routes = ['/', '/cuaderno/', '/libros/'];
const fragments = ['#%E0%A4%A', '#%ZZ', '#%'];
for (const [name, engine] of Object.entries({chromium, firefox, webkit})) {
  const browser = await engine.launch();
  try {
    for (const route of routes) for (const hash of fragments) {
      const page = await browser.newPage();
      const errors = [];
      page.on('pageerror', e => errors.push(e.message));
      await page.route(/^https?:\/\/(?!127\.0\.0\.1)/, r => r.abort());
      try {
        const response = await page.goto(origin + route + hash, {waitUntil: 'load'});
        assert.equal(response.status(), 200);
        await page.waitForTimeout(550);
        assert.deepEqual(errors, [], `${name} ${route}${hash}`);
        assert.equal(await page.locator('body').count(), 1);
        assert.ok(await page.locator('a[href]').count() > 0);
      } finally { await page.close(); }
    }
  } finally { await browser.close(); }
}
console.log('PASS malformed fragment recovery');