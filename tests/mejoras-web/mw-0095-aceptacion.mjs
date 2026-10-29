import assert from 'node:assert/strict';
import { chromium } from 'playwright';

// MW-0095: el boletín marca el email inválido con aria-invalid y lo retira al corregirlo.
const origin = process.env.SITE_ORIGIN;
assert.ok(origin, 'SITE_ORIGIN debe apuntar al servidor local del repositorio');

const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  await page.addInitScript(() => { try { localStorage.setItem('nl-subscribed', '1'); } catch (e) {} }); // sin ventana emergente del boletín
  await page.route('https://subscribe.davidpd89.workers.dev/**', route => route.fulfill({
    status: 200, contentType: 'application/json', headers: { 'access-control-allow-origin': '*' },
    body: JSON.stringify({ ok: true, state: 'pending_confirmation' }),
  }));
  await page.goto(`${origin.replace(/\/$/, '')}/cuaderno/`, { waitUntil: 'load', timeout: 20000 });
  const form = page.locator('#newsletter-form-cuaderno');
  await form.scrollIntoViewIfNeeded();
  const email = form.locator('input[type="email"]');
    assert.equal(await email.getAttribute('aria-invalid'), null, 'sin errores al cargar');
  // El campo ignora fill() repetidos en Chromium headless: se escribe el valor y se emite el evento input como lo haría el teclado.
  const setEmail = value => email.evaluate((el, v) => { el.value = v; el.dispatchEvent(new Event('input', { bubbles: true })); }, value);

  await setEmail('esto-no-es-un-email');
  await form.evaluate(f => f.requestSubmit());
  await page.waitForFunction(() => /válido/.test(document.querySelector('#newsletter-form-cuaderno [role="status"]')?.textContent || ''));
  assert.equal(await email.getAttribute('aria-invalid'), 'true', 'el campo inválido se anuncia con aria-invalid');
  assert.equal(await page.evaluate(() => document.activeElement?.type), 'email', 'el foco vuelve al email');

  await setEmail('lector@example.com');
  assert.equal(await email.getAttribute('aria-invalid'), null, 'al corregir el valor se retira aria-invalid');

  await setEmail('otra');
  await form.evaluate(f => f.requestSubmit());
  await page.waitForFunction(() => document.querySelector('#newsletter-form-cuaderno input[type="email"]')?.getAttribute('aria-invalid') === 'true');
  await setEmail('lector@example.com');
  await form.evaluate(f => f.requestSubmit());
  await page.waitForSelector('.quiz-subscribe-ok');
  console.log('PASS MW-0095: aria-invalid en email inválido, retirado al corregir; el envío válido sigue funcionando');
} finally {
  await browser.close();
}
