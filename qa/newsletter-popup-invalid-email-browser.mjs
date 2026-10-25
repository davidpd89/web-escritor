import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const PATH = '/cuaderno/que-es-el-portal-fantasy/';
const browser = await chromium.launch({ headless: true });

try {
  const context = await browser.newContext({ reducedMotion: 'reduce' });
  const page = await context.newPage();
  await page.addInitScript(() => {
    try {
      localStorage.removeItem('nl-popup-ts');
      localStorage.removeItem('nl-subscribed');
    } catch {}
  });
  const response = await page.goto(ORIGIN + PATH, { waitUntil: 'domcontentloaded' });
  assert.ok(response?.ok(), `${PATH}: página no disponible`);
  await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
  const dialog = page.locator('#nl-popup-dialog');
  await dialog.waitFor({ state: 'visible' });
  const email = dialog.locator('#nl-popup-email');
  await email.fill('correo-invalido');
  await dialog.locator('#nl-popup-submit').click();
  const status = dialog.locator('#nl-popup-status');
  await status.getByText(/Introduce un email válido/i).waitFor();
  const state = await email.evaluate(el => {
    const status = document.getElementById('nl-popup-status');
    const described = (el.getAttribute('aria-describedby') || '').split(/\s+/);
    const errorId = el.getAttribute('aria-errormessage');
    return {
      associated: described.includes(status?.id) || errorId === status?.id,
      invalid: el.getAttribute('aria-invalid') === 'true' || (!el.validity.valid && !el.form.noValidate),
      focused: document.activeElement === el,
      message: status?.textContent?.trim()
    };
  });
  assert.ok(state.associated, `${PATH}: ${JSON.stringify(state.message)} no está asociado a #nl-popup-email`);
  assert.ok(state.invalid, `${PATH}: el campo no comunica su invalidez`);
  assert.ok(state.focused, `${PATH}: el foco debe permitir corregir inmediatamente el correo`);
  await context.close();
} finally {
  await browser.close();
}
console.log('newsletter-popup-invalid-email-browser: PASS');
