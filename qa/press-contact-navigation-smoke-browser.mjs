import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const browser = await chromium.launch({ headless: true });

try {
  // With JS the header envelope opens the same mail chooser as the footer.
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));

  const response = await page.goto(ORIGIN + '/lectores-beta/', { waitUntil: 'load' });
  assert.ok(response?.ok(), `/lectores-beta/: HTTP ${response?.status()}`);

  const contact = page.locator('header a.header-contact:not(.header-social)');
  assert.equal(await contact.count(), 1, '/lectores-beta/: falta el enlace de contacto de cabecera');
  const href = await contact.getAttribute('href');
  assert.equal(href, '/prensa.html#contacto', `/lectores-beta/: fallback sin JS inesperado: ${href}`);

  await contact.click();
  assert.equal(await page.locator('.mail-chooser').count(), 1, 'Contacto: el sobre no abre el selector de correo');
  assert.equal(new URL(page.url()).pathname, '/lectores-beta/', `Contacto: el sobre navegó a ${page.url()}`);
  const copy = page.locator('.mail-chooser button');
  await copy.click();
  assert.equal(await copy.textContent(), 'Dirección copiada ✓', 'Contacto: «Copiar dirección» no responde al primer clic');
  assert.deepEqual(errors, [], `Contacto: errores JavaScript: ${errors.join('; ')}`);

  // Without JS it stays a real link to the press contact section.
  const ctx = await browser.newContext({ javaScriptEnabled: false });
  const noJs = await ctx.newPage();
  await noJs.goto(ORIGIN + '/lectores-beta/', { waitUntil: 'domcontentloaded' });
  await noJs.locator('header a.header-contact:not(.header-social)').click();
  await noJs.waitForURL('**/prensa.html#contacto');
  const target = noJs.locator('[id="contacto"], a[name="contacto"]');
  assert.ok(await target.count() > 0, '/prensa.html#contacto: fragmento sin destino real');
  assert.ok(await target.first().isVisible(), '/prensa.html#contacto: destino no visible');
  console.log('OK: sobre de cabecera (selector con JS, prensa sin JS)');
} finally {
  await browser.close();
}
