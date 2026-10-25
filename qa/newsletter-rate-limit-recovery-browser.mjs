import { chromium } from 'playwright';
import assert from 'node:assert/strict';

const base = process.env.BASE_URL || process.env.SITE_URL || 'http://127.0.0.1:8000';
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  let attempts = 0;
  await page.route('https://subscribe.davidpd89.workers.dev/**', async route => {
    attempts++;
    await route.fulfill(attempts === 1 ? { status: 429, contentType: 'application/json', body: '{}' } : { status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true, state: 'pending_confirmation' }) });
  });
  await page.goto(new URL('/lectores-beta/', base).href);
  await page.locator('[data-explore-open]').click();
  const form = page.locator('#newsletter-form-explore');
  const submit = form.locator('[type=submit]');
  await form.locator('input[type=email]').fill('lectora@example.com');
  await submit.click();
  await assert.doesNotReject(() => form.locator('[role=status]').getByText(/demasiados intentos/i).waitFor(), 'Explorar: falta el aviso de límite de solicitudes');
  assert.equal(await submit.isEnabled(), true, 'Explorar: botón bloqueado tras HTTP 429');
  assert.equal(await form.locator('input[type=email]').inputValue(), 'lectora@example.com', 'Explorar: correo perdido tras HTTP 429');
  await submit.click();
  await assert.doesNotReject(() => form.getByText(/revisa tu correo para confirmar/i).waitFor(), 'Explorar: no se recupera tras reintentar');
  assert.equal(attempts, 2, 'Explorar: número incorrecto de intentos');
} finally {
  await browser.close();
}
