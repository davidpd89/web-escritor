import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const ROUTE = '/las-manecillas-del-recuerdo/fragmentos/';
const browser = await chromium.launch({ headless: true });

try {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  await context.route('**/*', r => new URL(r.request().url()).origin === new URL(BASE).origin ? r.continue() : r.abort());
  await context.addInitScript(() => {
    Object.defineProperty(window, 'IntersectionObserver', { configurable: true, value: undefined });
  });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.goto(BASE + ROUTE + '#fragmento-2', { waitUntil: 'load' });
  assert.equal(await page.locator('.excerpt-section').count(), 3, 'Contenido desaparecido');
  assert.equal(await page.locator('[data-fragment-link="fragmento-2"]').getAttribute('data-current'), 'true', 'El hash inicial no selecciona el fragmento');
  await page.evaluate(() => { location.hash = '#fragmento-3'; });
  await page.waitForFunction(() => document.querySelector('[data-fragment-link="fragmento-3"]')?.dataset.current === 'true');
  assert.equal(await page.locator('[data-fragment-link][data-current="true"]').count(), 1, 'Estado de lectura duplicado');
  await page.evaluate(() => { location.hash = '#fragmento-inexistente'; });
  await page.waitForFunction(() => document.querySelectorAll('[data-fragment-link][data-current="true"]').length === 0);
  assert.deepEqual(errors, [], `Error sin IntersectionObserver: ${errors.join(' | ')}`);
  await context.close();
} finally {
  await browser.close();
}
console.log('PASS: fragmentos degradan correctamente');
