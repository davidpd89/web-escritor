import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const routes = ['/herramientas/eventos-ics/', '/herramientas/tiempo-lectura-voz-alta/', '/clubes-de-lectura/preparar-sesion/', '/herramientas/entrevista-familiar/', '/recursos/ficha-historia-objeto-heredado/'];
const common = ['v1-fonts.css', 'v1-tokens.css', 'v1-base.css', 'v1-shell.css', 'v1-components.css', 'v1-families.css', 'v1-tools.css', 'v1-tools-identity.css'];
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  let reference;
  for (const route of routes) {
    const page = await browser.newPage();
    const response = await page.goto(new URL(route, BASE).href, { waitUntil: 'networkidle' });
    assert.equal(response.status(), 200, `${route}: HTTP ${response.status()}`);
    const styles = await page.locator('link[rel="stylesheet"][href]').evaluateAll(els => els.map(el => new URL(el.href).pathname.split('/').pop()));
    const actual = common.filter(name => styles.includes(name));
    assert.deepEqual(actual, common, `${route}: falta CSS común: ${common.filter(name => !actual.includes(name)).join(', ')}`);
    for (const name of common) assert.equal(styles.filter(value => value === name).length, 1, `${route}: ${name} duplicado`);
    if (reference) assert.deepEqual(actual, reference, `${route}: divergencia de estilos comunes`);
    reference = actual;
    await page.close();
  }
} finally { await browser.close(); }
console.log('OK: paridad CSS de cinco herramientas');