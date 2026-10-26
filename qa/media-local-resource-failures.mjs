import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = (process.env.QA_ORIGIN || process.env.SITE_BASE_URL || 'http://127.0.0.1:4173').replace(/\/$/, '');
const routes = ['/libros/', '/libros/samuel-entre-mundos/', '/las-manecillas-del-recuerdo/'];
const types = new Set(['image', 'stylesheet', 'script', 'font']);
const browser = await chromium.launch({ headless: true });
try {
  for (const route of routes) {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 }, serviceWorkers: 'block' });
    const page = await context.newPage();
    const failures = [];
    const origin = new URL(BASE).origin;
    const local = request => types.has(request.resourceType()) && new URL(request.url()).origin === origin;
    page.on('requestfailed', request => {
      if (local(request)) failures.push(`${request.resourceType()} ${request.url()}: ${request.failure()?.errorText}`);
    });
    page.on('response', response => {
      const request = response.request();
      if (!local(request)) return;
      if (response.status() >= 400) failures.push(`${request.resourceType()} ${response.url()}: HTTP ${response.status()}`);
      if (response.status() === 200) {
        const length = response.headers()['content-length'];
        if (length === '0') failures.push(`${request.resourceType()} ${response.url()}: Content-Length=0`);
      }
    });
    try {
      const response = await page.goto(BASE + route, { waitUntil: 'load' });
      assert.equal(response?.status(), 200, `${route}: documento HTTP ${response?.status()}`);
      const images = page.locator('main img[loading="lazy"]');
      for (let i = 0; i < await images.count(); i++) {
        await images.nth(i).scrollIntoViewIfNeeded();
      }
      await page.evaluate(async () => {
        await Promise.all([...document.images].filter(img => img.loading === 'lazy').map(img => img.decode().catch(() => {})));
      });
      await page.evaluate(() => document.fonts.ready);
      assert.deepEqual(failures, [], `${route}: recursos locales fallidos: ${JSON.stringify(failures)}`);
    } finally {
      await context.close();
    }
  }
} finally {
  await browser.close();
}
console.log('PASS media-local-resource-failures');
