import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const routes = ['/herramientas/eventos-ics/', '/herramientas/tiempo-lectura-voz-alta/', '/clubes-de-lectura/preparar-sesion/', '/herramientas/entrevista-familiar/', '/recursos/ficha-historia-objeto-heredado/'];
const shared = ['/assets/email-reveal.js', '/assets/v1-shell.js'];
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  let reference;
  for (const route of routes) {
    const context = await browser.newContext();
    const page = await context.newPage();
    const requests = [];
    page.on('request', request => { if (request.resourceType() === 'script') requests.push(request.url()); });
    const response = await page.goto(new URL(route, BASE).href, { waitUntil: 'networkidle' });
    assert.equal(response.status(), 200, `${route}: HTTP ${response.status()}`);
    const versions = [];
    for (const script of shared) {
      const matches = requests.filter(url => new URL(url).pathname === script);
      assert.equal(matches.length, 1, `${route}: ${script} solicitado ${matches.length} veces`);
      versions.push(new URL(matches[0]).search);
    }
    if (reference) assert.deepEqual(versions, reference, `${route}: versiones distintas de scripts compartidos`);
    reference = versions;
    await context.close();
  }
} finally { await browser.close(); }
console.log('OK: scripts compartidos sin duplicaciones');