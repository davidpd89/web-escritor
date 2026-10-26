import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  const response = await page.goto(`${ORIGIN}/editoriales/`, { waitUntil: 'networkidle' });
  assert.equal(response?.ok(), true, '/editoriales/: error HTTP inicial');
  const cards = page.locator('[data-editorial-card]');
  const initial = await cards.count();
  assert.ok(initial > 0, '/editoriales/: directorio vacío');
  const firstName = await cards.first().getAttribute('data-name');
  assert.ok(firstName, '/editoriales/: primera editorial sin nombre');
  const search = page.locator('[data-editoriales-search]');
  const requests = [];
  page.on('request', request => requests.push(request.url()));
  await search.fill(firstName);
  await assertVisible(page, true);
  await search.fill('zzzzeditorialinexistentezzzz');
  await assertVisible(page, false);
  await page.locator('[data-editoriales-reset]').click();
  await page.waitForFunction(expected => document.querySelectorAll('[data-editorial-card]:not([hidden])').length === expected, initial);
  assert.equal(await search.inputValue(), '', '/editoriales/: reinicio conserva búsqueda');
  assert.deepEqual(requests, [], `/editoriales/: filtros generaron ${requests.length} peticiones: ${requests.join(', ')}`);
  console.log('editoriales-filter-network-budget: PASS');
} finally {
  await browser.close();
}

async function assertVisible(page, expected) {
  await page.waitForFunction(value => {
    const count = document.querySelectorAll('[data-editorial-card]:not([hidden])').length;
    return value ? count > 0 : count === 0;
  }, expected);
  const count = await page.locator('[data-editorial-card]:not([hidden])').count();
  const label = await page.locator('[data-editoriales-count]').innerText();
  assert.match(label, new RegExp(`^${count} editoriales?`), `/editoriales/: contador incorrecto: ${label}`);
}