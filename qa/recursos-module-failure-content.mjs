import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const ROUTE = '/recursos/ficha-historia-objeto-heredado/';
const browser = await chromium.launch({headless:true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});

try {
  const context = await browser.newContext();
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(String(error)));
  await page.route('**/assets/objeto-heredado.js?*', route => route.abort('failed'));
  const response = await page.goto(BASE + ROUTE, {waitUntil:'load'});
  assert.ok(response?.ok(), `${ROUTE}: no carga el documento tras bloquear el módulo`);
  assert.match(await page.locator('main h1').innerText(), /objeto heredado/i, `${ROUTE}: falta el título`);
  assert.match(await page.locator('main').innerText(), /Privacidad:/, `${ROUTE}: falta la explicación de privacidad`);
  const sections = await page.locator('main .tool-findings-block h3').allTextContents();
  assert.equal(sections.length, 8, `${ROUTE}: faltan secciones documentales tras fallar el módulo: ${JSON.stringify(sections)}`);
  for (const id of ['object-title','object-type','object-materials','object-marks','object-open-questions']) {
    assert.equal(await page.locator(`#${id}`).count(), 1, `${ROUTE}: falta el campo estático ${id}`);
  }
  assert.deepEqual(errors, [], `${ROUTE}: errores JS no controlados: ${errors.join(' | ')}`);
  console.log('OK recursos-module-failure-content');
} finally {
  await browser.close();
}
