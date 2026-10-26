import test from 'node:test';
import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = process.env.BASE_URL || process.env.TEST_BASE_URL || 'http://127.0.0.1:8000';

test('accesibilidad: privacidad y contrato JSON del formulario Explorar', async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage();
    let payload = null;
    await page.route('**/subscribe.davidpd89.workers.dev/**', async route => {
      payload = route.request().postDataJSON();
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true, state: 'pending_confirmation' }) });
    });
    await page.goto(new URL('/accesibilidad/', base).href);
    await page.locator('[data-explore-open]').click();
    const form = page.locator('#newsletter-form-explore');
    const privacy = form.locator('a[href]');
    assert.equal(await privacy.count(), 1, '/accesibilidad/: debe existir un enlace de privacidad asociado al formulario');
    const href = await privacy.getAttribute('href');
    assert.equal(new URL(href, base).pathname, '/privacidad.html', '/accesibilidad/: destino de privacidad incorrecto');
    const response = await page.request.get(new URL(href, base).href);
    assert.equal(response.status(), 200, '/accesibilidad/: política de privacidad no disponible');
    await form.locator('input[type=email]').fill('lectora@example.com');
    await form.locator('button[type=submit]').click();
    await page.getByText(/solicitud recibida/i).waitFor();
    assert.ok(payload, '/accesibilidad/: no se observó la petición JSON');
    assert.deepEqual(Object.keys(payload).sort(), ['email', 'source', 'website'], '/accesibilidad/: campos inesperados en la petición');
    assert.equal(payload.email, 'lectora@example.com');
    assert.equal(payload.source, 'explore');
    assert.equal(payload.website, '');
  } finally {
    await browser.close();
  }
});