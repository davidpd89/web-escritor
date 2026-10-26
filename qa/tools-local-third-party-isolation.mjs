import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const BASE = new URL(ORIGIN);
const ROUTES = [
  '/herramientas/contador-palabras/',
  '/herramientas/limpiador-manuscritos/',
  '/herramientas/dialogo-convenciones/',
  '/herramientas/nombres-personajes/',
];

const browser = await chromium.launch({
  headless: true,
  ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}),
});
try {
  for (const route of ROUTES) {
    const context = await browser.newContext({ serviceWorkers: 'block' });
    const page = await context.newPage();
    const external = [];
    page.on('request', request => {
      const url = new URL(request.url());
      if (url.origin !== BASE.origin) {
        external.push({ url: request.url(), method: request.method() });
      }
    });
    const response = await page.goto(new URL(route, BASE).href, { waitUntil: 'networkidle' });
    assert.equal(response?.status(), 200, `${route}: respuesta HTTP inesperada`);
    assert.equal(await page.locator('h1').count(), 1, `${route}: documento de herramienta no cargado`);
    assert.deepEqual(external, [], `${route}: peticiones externas observadas: ${JSON.stringify(external)}`);
    await context.close();
  }
  console.log(`OK: ${ROUTES.length} herramientas sin peticiones iniciales a terceros`);
} finally {
  await browser.close();
}
