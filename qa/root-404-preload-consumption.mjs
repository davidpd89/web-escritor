import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = (process.env.SITE_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const browser = await chromium.launch({ headless: true });

try {
  const page = await browser.newPage();
  const response = await page.goto(`${BASE}/404.html`, { waitUntil: 'load' });
  assert.equal(response?.status(), 200, '404.html: no se pudo cargar el documento de prueba');
  const result = await page.evaluate(() => {
    const absolute = value => new URL(value, location.href).href;
    const preloads = [...document.querySelectorAll('link[rel~=preload][as=style]')].map(link => absolute(link.href));
    const sheets = [...document.styleSheets].map(sheet => sheet.href).filter(Boolean);
    const loaded = new Set(sheets.map(absolute));
    const unused = preloads.filter(url => !loaded.has(url));
    return { preloads, unused };
  });
  assert.ok(result.preloads.length, '404.html: no se encontraron las precargas CSS esperadas; revisar el contrato de prueba');
  assert.deepEqual(result.unused, [], `404.html: precargas CSS sin hoja de estilo consumidora: ${result.unused.join(', ')}`);
  console.log(`PASS: ${result.preloads.length} precargas CSS consumidas en 404.html`);
} finally {
  await browser.close();
}
