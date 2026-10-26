import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const ROUTE = '/recursos/ficha-historia-objeto-heredado/';
const SENTINEL = 'QA_OBJETO_PRIVADO_582931';
const browser = await chromium.launch({headless:true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});

try {
  const context = await browser.newContext();
  const page = await context.newPage();
  const outgoing = [];
  page.on('request', request => {
    if (request.isNavigationRequest() || request.method() !== 'GET') outgoing.push({url:request.url(),method:request.method(),body:request.postData() || ''});
  });
  await page.route('**/assets/objeto-heredado.js?*', route => route.abort('failed'));
  const response = await page.goto(BASE + ROUTE, {waitUntil:'load'});
  assert.ok(response?.ok(), `${ROUTE}: documento no disponible`);
  outgoing.length = 0;
  await page.locator('#object-title').fill(SENTINEL);
  await page.locator('#object-title').press('Enter');
  assert.equal(new URL(page.url()).pathname, ROUTE, `${ROUTE}: Intro abandona la ficha al fallar el módulo`);
  assert.equal(await page.locator('#object-title').inputValue(), SENTINEL, `${ROUTE}: se pierde el texto introducido`);
  assert.deepEqual(outgoing.filter(r => r.body.includes(SENTINEL) || r.url.includes(SENTINEL)), [], `${ROUTE}: se transmitieron datos privados: ${JSON.stringify(outgoing)}`);
  console.log('OK recursos-form-failure-egress');
} finally {
  await browser.close();
}
