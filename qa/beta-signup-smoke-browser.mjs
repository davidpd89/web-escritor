import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const route = '/lectores-beta/';
const browser = await chromium.launch({ headless: true });

try {
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));

  const response = await page.goto(ORIGIN + route, { waitUntil: 'domcontentloaded' });
  assert.ok(response?.ok(), `${route}: HTTP ${response?.status()}`);

  const form = page.locator('#lectores-beta-form');
  await form.waitFor({ state: 'visible' });
  const email = form.locator('input[type="email"]');
  assert.equal(await email.count(), 1, `${route}: debe existir exactamente un campo de correo en el formulario beta`);
  assert.ok(await email.isEnabled(), `${route}: campo de correo deshabilitado`);

  await email.focus();
  assert.ok(await email.evaluate(el => document.activeElement === el), `${route}: el correo no recibe foco`);
  await email.fill('lectora@example.com');
  assert.equal(await email.inputValue(), 'lectora@example.com', `${route}: no se puede editar el correo`);
  assert.deepEqual(errors, [], `${route}: errores JavaScript: ${errors.join('; ')}`);
  console.log('OK: inscripción beta disponible');
} finally {
  await browser.close();
}
