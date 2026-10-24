import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
try {
  for (const [route, id] of [
    ['/fragmento/', 'newsletter-form-fragmento'],
    ['/cuaderno/', 'newsletter-form-cuaderno']
  ]) {
    const context = await browser.newContext({ javaScriptEnabled: false });
    await context.route(/^https?:/, r => r.request().url().startsWith(BASE) ? r.continue() : r.abort());
    const page = await context.newPage();
    const sentinel = 'private-leak-probe@example.test';
    const requests = [];
    page.on('request', r => requests.push(r.url()));
    await page.goto(BASE + route, { waitUntil: 'load' });
    const form = page.locator('#' + id);
    assert.equal(await form.count(), 1);
    await form.locator('input[type="email"]').fill(sentinel);
    const submit = form.locator('[type="submit"]');
    if (await submit.isEnabled()) {
      await submit.click({ timeout: 3000 });
      await page.waitForLoadState('domcontentloaded').catch(() => {});
    }
    assert(!page.url().includes(sentinel), route + ': correo incluido en URL de navegación');
    assert(!requests.some(url => decodeURIComponent(url).includes(sentinel)), route + ': correo transmitido por URL GET');
    await context.close();
  }
} finally {
  await browser.close();
}
console.log('audit-newsletter-nojs-email-leak: PASS');