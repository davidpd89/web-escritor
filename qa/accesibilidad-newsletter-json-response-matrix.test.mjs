import test from 'node:test';
import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = process.env.BASE_URL || process.env.TEST_BASE_URL || 'http://127.0.0.1:8000';
const cases = [
  { name: 'pendiente válida', status: 200, body: { ok: true, state: 'pending_confirmation' }, success: true },
  { name: 'HTTP 200 sin confirmación pendiente', status: 200, body: { ok: true }, success: false },
  { name: 'HTTP 200 con rechazo explícito', status: 200, body: { ok: false }, success: false },
  { name: 'petición inválida', status: 400, body: { ok: false }, success: false },
  { name: 'límite de solicitudes', status: 429, body: { ok: false }, success: false },
  { name: 'error de servidor', status: 500, body: { ok: false }, success: false }
];

for (const scenario of cases) {
  test(`accesibilidad: respuesta newsletter ${scenario.name}`, async () => {
    const browser = await chromium.launch({ headless: true });
    try {
      const page = await browser.newPage();
      await page.route('**/subscribe.davidpd89.workers.dev/**', route => route.fulfill({ status: scenario.status, contentType: 'application/json', body: JSON.stringify(scenario.body) }));
      await page.goto(new URL('/accesibilidad/', base).href);
      await page.locator('[data-explore-open]').click();
      const form = page.locator('#newsletter-form-explore');
      await form.locator('input[type=email]').fill('lectora@example.com');
      await form.locator('button[type=submit]').click();
      if (scenario.success) {
        await page.getByText(/solicitud recibida/i).waitFor();
        assert.equal(await form.locator('input[type=email]').count(), 0, `/accesibilidad/: ${scenario.name}: el formulario no pasó al estado pendiente`);
      } else {
        await form.locator('[role=status]').filter({ hasText: /error|inténtalo|espera/i }).waitFor();
        assert.equal(await form.locator('input[type=email]').count(), 1, `/accesibilidad/: ${scenario.name}: se perdió el campo de correo`);
        assert.equal(await form.locator('button[type=submit]').isEnabled(), true, `/accesibilidad/: ${scenario.name}: no permite reintentar`);
        assert.equal(await form.getByText(/solicitud recibida/i).count(), 0, `/accesibilidad/: ${scenario.name}: confirmación falsa`);
      }
    } finally {
      await browser.close();
    }
  });
}