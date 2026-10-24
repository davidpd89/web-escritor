import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
try {
  for (const route of ['/cuaderno/', '/cuaderno/portal-fantasy-vs-fantasia-epica/']) {
    const context = await browser.newContext();
    await context.route('**/*', r => new URL(r.request().url()).origin === new URL(BASE).origin ? r.continue() : r.abort());
    await context.addInitScript(() => localStorage.setItem('nl-popup-ts', String(Date.now())));
    const page = await context.newPage();
    let requests = 0;
    let release;
    const blocked = new Promise(resolve => { release = resolve; });
    await page.route('https://subscribe.davidpd89.workers.dev/**', async r => {
      requests++;
      await blocked;
      await r.fulfill({ status: 503, contentType: 'application/json', body: '{"ok":false}' });
    });
    try {
      await page.goto(BASE + route);
      const form = page.locator('#newsletter-form-cuaderno');
      await form.locator('input[type=email]').fill('qa-parallel@example.com');
      await form.locator('[type=submit]').click();
      await page.waitForFunction(() => document.querySelector('#newsletter-form-cuaderno [type=submit]')?.disabled);
      await form.evaluate(el => { for (let i = 0; i < 4; i++) el.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })); });
      assert.equal(requests, 1, `${route}: solicitudes simultáneas`);
      release();
      await page.waitForFunction(() => document.querySelector('#newsletter-form-cuaderno [type=submit]')?.disabled === false);
      assert.match(await form.innerText(), /Error al suscribirse/i);
      assert.equal(requests, 1);
    } finally { release(); await context.close(); }
  }
  console.log('PASS newsletter concurrent-submit idempotence');
} finally { await browser.close(); }
