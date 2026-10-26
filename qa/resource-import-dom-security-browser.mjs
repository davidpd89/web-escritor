import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const route = '/recursos/ficha-historia-objeto-heredado/';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

try {
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(String(error)));
  await page.goto(new URL(route, BASE).href, { waitUntil: 'load' });
  await page.locator('[data-record-status]').waitFor();

  const payload = '<img src=x onerror=alert(1)> Ficha familiar';
  const record = {
    schema_version: 1,
    object: { title: payload, marks: '<svg onload=alert(2)>' },
    photos: [], owners: [], evidence: [], oral_history: [], timeline: [],
    open_questions: [payload]
  };

  await page.locator('[data-record-import]').setInputFiles({
    name: 'ficha-familiar.json',
    mimeType: 'application/json',
    buffer: Buffer.from(JSON.stringify(record))
  });

  await page.waitForFunction(() => document.querySelector('[data-record-status]')?.textContent?.includes('cargado'));
  assert.equal(await page.locator('[data-object-field="title"]').inputValue(), payload, `${route}: título importado alterado`);
  assert.equal(await page.locator('[data-object-field="marks"]').inputValue(), '<svg onload=alert(2)>', `${route}: marcas importadas alteradas`);
  assert.equal(await page.locator('[data-open-questions]').inputValue(), payload, `${route}: preguntas importadas alteradas`);
  assert.equal(await page.locator('img[onerror], svg[onload], script[src="x"]').count(), 0, `${route}: la importación creó nodos ejecutables`);
  assert.deepEqual(errors, [], `${route}: errores JavaScript tras importar: ${errors.join(' | ')}`);
  console.log('PASS resource import DOM security');
} finally {
  await browser.close();
}
