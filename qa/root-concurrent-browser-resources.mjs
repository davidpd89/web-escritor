import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE = (process.env.SITE_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const ROUTES = ['/', '/autor.html', '/prensa.html', '/libros/', '/herramientas/', '/cuaderno/'];
const browser = await chromium.launch({headless: true});
const failures = [];

try {
  await Promise.all(ROUTES.map(async route => {
    const context = await browser.newContext({viewport: {width: 1280, height: 800}, serviceWorkers: 'block'});
    const page = await context.newPage();
    const pending = [];
    try {
      await page.route('**/*', request => {
        const url = new URL(request.request().url());
        if (url.origin !== BASE) return request.abort();
        return request.continue();
      });
      page.on('response', response => {
        const url = new URL(response.url());
        if (url.origin !== BASE || !/\.(?:css|js|mjs|png|jpe?g|webp|avif|svg|woff2)(?:$)/i.test(url.pathname)) return;
        pending.push((async () => {
          try {
            assert.equal(response.status(), 200, `${route}: ${url.pathname} HTTP ${response.status()}`);
            const bytes = await response.body();
            assert.ok(bytes.length > 0, `${route}: ${url.pathname} vacío`);
          } catch (error) {
            failures.push(`${route}: ${error.message}`);
          }
        })());
      });
      page.on('requestfailed', request => {
        const url = new URL(request.url());
        if (url.origin === BASE) failures.push(`${route}: petición fallida ${url.pathname}: ${request.failure()?.errorText}`);
      });
      const navigation = await page.goto(new URL(route, BASE).href, {waitUntil: 'load', timeout: 25000});
      assert.equal(navigation?.status(), 200, `${route}: documento HTTP ${navigation?.status()}`);
      await Promise.all(pending);
    } catch (error) {
      failures.push(`${route}: ${error.message}`);
    } finally {
      await context.close();
    }
  }));
} finally {
  await browser.close();
}

assert.deepEqual(failures, [], failures.join('\n'));
console.log(`PASS: ${ROUTES.length} navegaciones concurrentes sin fallos de recursos locales`);
