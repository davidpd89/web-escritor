import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const CASES = [
  ['/fragmento/', 'fragmento'],
  ['/cuaderno/', 'cuaderno']
];
const STATUSES = [400, 429, 500];
const browser = await chromium.launch();
try {
  for (const [path, source] of CASES) {
    for (const statusCode of STATUSES) {
      const context = await browser.newContext({ serviceWorkers: 'block' });
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await context.route('**/*', route => {
        if (route.request().url().startsWith('https://subscribe.davidpd89.workers.dev/')) {
          return route.fulfill({ status: statusCode, contentType: 'text/html', body: '<img src=x onerror=alert(1)>' });
        }
        if (new URL(route.request().url()).origin !== ORIGIN) return route.abort();
        return route.continue();
      });
      try {
        const response = await page.goto(ORIGIN + path, { waitUntil: 'domcontentloaded' });
        assert.ok(response?.ok(), `${path}: navigation HTTP ${response?.status()}`);
        const form = page.locator('#newsletter-form-' + source);
        const status = page.locator('#nl-status-' + source);
        await page.locator('#nl-email-' + source).fill('qa-error@example.com');
        await form.locator('[type=submit]').click();
        await assert.doesNotReject(() => status.getByText(/Inténtalo|Espera/i).waitFor({ timeout: 10000 }), `${path}: HTTP ${statusCode} must produce a recoverable error`);
        assert.equal(await page.locator('img[onerror]').count(), 0, `${path}: HTTP ${statusCode} injected executable HTML`);
        assert.equal(await form.locator('[type=submit]').isEnabled(), true, `${path}: HTTP ${statusCode} disabled retry`);
        assert.deepEqual(errors, [], `${path}: HTTP ${statusCode} uncaught errors`);
      } finally {
        await context.close();
      }
    }
  }
} finally {
  await browser.close();
}
console.log('PASS: subscription error DOM boundary');
