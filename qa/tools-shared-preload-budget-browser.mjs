import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const routes = ['/herramientas/eventos-ics/', '/herramientas/tiempo-lectura-voz-alta/', '/clubes-de-lectura/preparar-sesion/', '/herramientas/entrevista-familiar/', '/recursos/ficha-historia-objeto-heredado/'];
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  let reference;
  for (const route of routes) {
    const page = await browser.newPage();
    const response = await page.goto(new URL(route, BASE).href, { waitUntil: 'networkidle' });
    assert.equal(response.status(), 200, `${route}: HTTP ${response.status()}`);
    const preloads = await page.locator('link[rel="preload"][as="style"][href]').evaluateAll(els => els.map(el => new URL(el.href).pathname).sort());
    assert.equal(new Set(preloads).size, preloads.length, `${route}: precargas CSS duplicadas: ${JSON.stringify(preloads)}`);
    assert.ok(preloads.length <= 9, `${route}: ${preloads.length} precargas CSS; presupuesto máximo 9`);
    if (reference) assert.deepEqual(preloads, reference, `${route}: precargas del shell distintas del resto de herramientas`);
    reference = preloads;
    await page.close();
  }
} finally { await browser.close(); }
console.log('OK: presupuesto de precargas homogéneo');