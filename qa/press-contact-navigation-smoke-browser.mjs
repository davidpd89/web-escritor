import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const browser = await chromium.launch({ headless: true });

try {
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));

  const response = await page.goto(ORIGIN + '/lectores-beta/', { waitUntil: 'domcontentloaded' });
  assert.ok(response?.ok(), `/lectores-beta/: HTTP ${response?.status()}`);

  const contact = page.locator('header a.header-contact');
  assert.equal(await contact.count(), 1, '/lectores-beta/: falta el enlace de contacto de cabecera');
  const href = await contact.getAttribute('href');
  assert.equal(href, '/prensa.html#contacto', `/lectores-beta/: destino de contacto inesperado: ${href}`);

  await contact.click();
  await page.waitForURL('**/prensa.html#contacto');
  assert.equal(new URL(page.url()).pathname, '/prensa.html', `Contacto: ruta incorrecta ${page.url()}`);

  const target = page.locator('[id="contacto"], a[name="contacto"]');
  assert.ok(await target.count() > 0, '/prensa.html#contacto: fragmento sin destino real');
  assert.ok(await target.first().isVisible(), '/prensa.html#contacto: destino no visible');
  assert.deepEqual(errors, [], `Contacto de prensa: errores JavaScript: ${errors.join('; ')}`);
  console.log('OK: navegación a contacto');
} finally {
  await browser.close();
}
