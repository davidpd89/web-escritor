import { chromium } from 'playwright';
import assert from 'node:assert/strict';

const base = process.env.BASE_URL || process.env.SITE_URL || 'http://127.0.0.1:8000';
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  const payloads = [];
  await page.route('https://subscribe.davidpd89.workers.dev/**', async route => {
    payloads.push(JSON.parse(route.request().postData()));
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true, state: 'pending_confirmation' }) });
  });
  await page.goto(new URL('/lectores-beta/', base).href);
  await page.locator('[data-explore-open]').click();
  const form = page.locator('#newsletter-form-explore');
  await form.locator('input[type=email]').fill('lectora@example.com');
  await form.locator('[type=submit]').click();
  await assert.doesNotReject(() => form.getByText(/revisa tu correo para confirmar/i).waitFor(), 'Explorar: no se muestra la confirmación pendiente');
  assert.equal(payloads.length, 1, 'Explorar: número incorrecto de solicitudes');
  assert.equal(payloads[0].email, 'lectora@example.com', 'Explorar: correo transmitido incorrecto');
  assert.equal(payloads[0].source, 'explore', 'Explorar: origen de conversión incorrecto');
  assert.equal(payloads[0].website, '', 'Explorar: honeypot legítimo incorrecto');
} finally {
  await browser.close();
}
