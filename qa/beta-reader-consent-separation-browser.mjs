import { chromium } from 'playwright';
import assert from 'node:assert/strict';

const base = process.env.BASE_URL || process.env.SITE_URL || 'http://127.0.0.1:8000';
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  await page.goto(new URL('/lectores-beta/', base).href);
  const beta = page.locator('#lectores-beta-form');
  const consent = beta.locator('input[name=consent]');
  assert.equal(await beta.count(), 1, '/lectores-beta/: falta el formulario beta');
  assert.equal(await consent.count(), 1, '/lectores-beta/: falta el consentimiento específico');
  assert.equal(await consent.isChecked(), false, '/lectores-beta/: consentimiento premarcado');
  assert.equal(await consent.getAttribute('required') !== null, true, '/lectores-beta/: consentimiento no obligatorio');
  const label = page.locator('label[for=lectores-beta-gdpr]');
  assert.match(await label.innerText(), /lectores beta/i, '/lectores-beta/: consentimiento sin finalidad específica');
  assert.match(await label.innerText(), /lista separada/i, '/lectores-beta/: no se informa de la separación de listas');
  assert.equal(await beta.locator('input[type=email]').count(), 1, '/lectores-beta/: falta el correo de inscripción');
  await page.locator('[data-explore-open]').click();
  const general = page.locator('#newsletter-form-explore');
  assert.equal(await general.count(), 1, '/lectores-beta/: falta la newsletter general independiente');
  assert.equal(await general.locator('input[name=consent]').count(), 0, '/lectores-beta/: la newsletter general reutiliza el consentimiento beta');
  assert.equal(await consent.isChecked(), false, '/lectores-beta/: abrir la newsletter general modificó el consentimiento beta');
} finally {
  await browser.close();
}
