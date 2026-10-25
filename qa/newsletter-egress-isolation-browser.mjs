import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const WORKER = 'https://subscribe.davidpd89.workers.dev';
const CASES = [
  ['/fragmento/', '#newsletter-form-fragmento', '#nl-email-fragmento'],
  ['/las-manecillas-del-recuerdo/', '#newsletter-form-manecillas', '#nl-email-manecillas'],
  ['/cuaderno/', '#newsletter-form-cuaderno', '#nl-email-cuaderno']
];
const browser = await chromium.launch({ headless: true });
try {
  for (const [path, form, input] of CASES) {
    const context = await browser.newContext({ serviceWorkers: 'block' });
    const page = await context.newPage();
    const email = 'qa-egress@example.com';
    const leaks = [];
    const workerRequests = [];
    await context.route('**/*', async route => {
      const request = route.request();
      const url = new URL(request.url());
      const serialized = JSON.stringify({ url: request.url(), headers: request.headers(), body: request.postData() });
      if (url.origin === WORKER) {
        workerRequests.push(request);
        return route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify({ ok: true, state: 'pending_confirmation' }) });
      }
      if (serialized.includes(email)) leaks.push(request.url());
      if (url.origin !== ORIGIN) return route.abort();
      return route.continue();
    });
    try {
      const response = await page.goto(ORIGIN + path, { waitUntil: 'domcontentloaded' });
      assert.ok(response?.ok(), `${path}: HTTP ${response?.status()}`);
      await page.locator(input).fill(email);
      await page.locator(form + ' [type=submit]').click();
      await page.waitForFunction(selector => /Revisa tu correo/i.test(document.querySelector(selector)?.textContent || ''), form);
      assert.equal(workerRequests.length, 1, `${path}: expected one authorized subscription request`);
      assert.deepEqual(leaks, [], `${path}: email leaked to unauthorized requests: ${leaks.join(', ')}`);
      assert.ok(!page.url().includes(email), `${path}: email exposed in navigation URL`);
    } finally {
      await context.close();
    }
  }
} finally {
  await browser.close();
}
console.log('PASS: newsletter email egress isolation');
