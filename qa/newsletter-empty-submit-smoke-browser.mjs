import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const route = '/cuaderno/que-es-el-portal-fantasy/';
const browser = await chromium.launch({ headless: true });

try {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, serviceWorkers: 'block' });
  await context.route('**/*', request => {
    const url = new URL(request.request().url());
    return url.origin === ORIGIN ? request.continue() : request.abort();
  });
  const page = await context.newPage();
  const errors = [];
  const submissions = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => {
    if (request.method() === 'POST') submissions.push(request.url());
  });

  const response = await page.goto(ORIGIN + route, { waitUntil: 'domcontentloaded' });
  assert.ok(response?.ok(), `${route}: HTTP ${response?.status()}`);

  await page.evaluate(async () => {
    const frame = () => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    scrollTo({ top: document.documentElement.scrollHeight, behavior: 'instant' });
    await frame();
  });

  const dialog = page.locator('#nl-popup-dialog[open]');
  await dialog.waitFor({ state: 'visible' });
  const email = dialog.locator('#nl-popup-email');
  await email.fill('');
  await dialog.locator('#nl-popup-submit').click();

  const status = dialog.locator('#nl-popup-status');
  await assert.doesNotReject(() => status.getByText('Introduce un email válido.').waitFor({ state: 'visible' }), `${route}: falta mensaje de validación de correo vacío`);
  assert.equal(submissions.length, 0, `${route}: se enviaron ${submissions.length} solicitudes POST sin correo`);
  assert.ok(await email.isEnabled(), `${route}: correo bloqueado tras error`);
  assert.ok(await dialog.locator('#nl-popup-submit').isEnabled(), `${route}: botón bloqueado tras error`);
  await email.fill('lectora@example.com');
  assert.equal(await email.inputValue(), 'lectora@example.com', `${route}: no permite corregir el correo`);
  assert.deepEqual(errors, [], `${route}: errores JavaScript: ${errors.join('; ')}`);
  console.log('OK: validación recuperable de correo vacío');
} finally {
  await browser.close();
}
