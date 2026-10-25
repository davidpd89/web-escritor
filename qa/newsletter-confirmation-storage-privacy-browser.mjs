import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const CASES = [
  ['/fragmento/', 'fragmento'],
  ['/cuaderno/', 'cuaderno'],
  ['/las-manecillas-del-recuerdo/', 'manecillas']
];
const browser = await chromium.launch();
try {
  for (const [path, source] of CASES) {
    const context = await browser.newContext({ serviceWorkers: 'block' });
    const page = await context.newPage();
    const email = `qa-private-${source}@example.com`;
    await context.route('**/*', route => {
      if (route.request().url().startsWith('https://subscribe.davidpd89.workers.dev/')) {
        return route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify({ ok: true, state: 'pending_confirmation' }) });
      }
      if (new URL(route.request().url()).origin !== ORIGIN) return route.abort();
      return route.continue();
    });
    try {
      const response = await page.goto(ORIGIN + path, { waitUntil: 'domcontentloaded' });
      assert.ok(response?.ok(), `${path}: HTTP ${response?.status()}`);
      await page.locator('#nl-email-' + source).fill(email);
      await page.locator('#newsletter-form-' + source + ' [type=submit]').click();
      await page.waitForFunction(selector => /Revisa tu correo/i.test(document.querySelector(selector)?.textContent || ''), '#newsletter-form-' + source);
      const result = await page.evaluate(() => {
        const entries = storage => Object.fromEntries(Array.from({ length: storage.length }, (_, i) => {
          const key = storage.key(i);
          return [key, storage.getItem(key)];
        }));
        return { local: entries(localStorage), session: entries(sessionStorage), url: location.href };
      });
      assert.ok(!JSON.stringify(result).includes(email), `${path}: email persisted in browser state`);
      await page.reload({ waitUntil: 'domcontentloaded' });
      const persisted = await page.evaluate(() => JSON.stringify({ local: { ...localStorage }, session: { ...sessionStorage }, url: location.href }));
      assert.ok(!persisted.includes(email), `${path}: email survived navigation reload`);
    } finally {
      await context.close();
    }
  }
} finally {
  await browser.close();
}
console.log('PASS: subscription confirmation storage privacy');
