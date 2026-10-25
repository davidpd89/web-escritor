import { chromium } from 'playwright';
import assert from 'node:assert/strict';

const base = process.env.BASE_URL || process.env.SITE_URL || 'http://127.0.0.1:8000';
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  let requests = 0;
  await page.route('https://subscribe.davidpd89.workers.dev/**', async route => {
    requests++;
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true, state: 'pending_confirmation' }) });
  });
  await page.goto(new URL('/lectores-beta/', base).href);
  await page.locator('[data-explore-open]').click();
  const form = page.locator('#newsletter-form-explore');
  await form.locator('input[type=email]').fill('correo-invalido');
  await form.locator('[type=submit]').click();
  await assert.doesNotReject(() => form.locator('[role=status]').getByText(/email válido/i).waitFor(), 'Explorar: falta el mensaje de correo inválido');
  assert.equal(requests, 0, 'Explorar: un correo inválido ha generado solicitudes');
  assert.equal(await form.locator('input[type=email]').inputValue(), 'correo-invalido', 'Explorar: se perdió el valor editable');
} finally {
  await browser.close();
}
