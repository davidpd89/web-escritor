import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const routes = ['/cuaderno/', '/cuaderno/que-es-el-portal-fantasy/', '/cuaderno/feria-libro-madrid-2026-samuel-entre-mundos/'];
const browser = await chromium.launch({ headless: true });
try {
  for (const route of routes) {
    const context = await browser.newContext();
    await context.route('**/*', r => {
      const url = r.request().url();
      if (url.startsWith('https://subscribe.davidpd89.workers.dev')) return r.fallback();
      return new URL(url).origin === new URL(BASE).origin ? r.continue() : r.abort();
    });
    await context.addInitScript(() => localStorage.setItem('nl-popup-ts', String(Date.now())));
    const page = await context.newPage();
    let requests = 0;
    await page.route('https://subscribe.davidpd89.workers.dev/**', async r => {
      requests++;
      const status = requests === 1 ? 429 : 201;
      await r.fulfill({ status, contentType: 'application/json', body: JSON.stringify(status === 429 ? { ok: false } : { ok: true, state: 'pending_confirmation' }) });
    });
    try {
      await page.goto(BASE + route);
      const form = page.locator('#newsletter-form-cuaderno');
      const email = form.locator('input[type=email]');
      await email.fill('correo-invalido');
      await form.locator('[type=submit]').click();
      assert.equal(requests, 0, `${route}: email inválido enviado`);
      assert.match(await form.innerText(), /Introduce un email válido/i);
      await email.fill('qa-cuaderno@example.com');
      await form.locator('[type=submit]').click();
      await page.waitForFunction(() => document.querySelector('#nl-status-cuaderno')?.textContent.includes('demasiados intentos'));
      assert.equal(requests, 1, route);
      assert.equal(await form.locator('[type=submit]').isDisabled(), false, route);
      await form.locator('[type=submit]').click();
      await page.waitForFunction(() => document.querySelector('#newsletter-form-cuaderno')?.textContent.includes('Revisa tu correo'));
      assert.equal(requests, 2, `${route}: reintento duplicado`);
    } finally { await context.close(); }
  }
  console.log('PASS cuaderno newsletter retry');
} finally { await browser.close(); }
