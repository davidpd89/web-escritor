import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
const context = await browser.newContext({ viewport: { width: 390, height: 900 } });
const page = await context.newPage();
const pageErrors = [];
page.on('pageerror', error => pageErrors.push(error.message));

try {
  await page.goto(`${origin}/las-manecillas-del-recuerdo/fragmentos/#%E0%A4%A`, { waitUntil: 'load' });
  await page.waitForTimeout(100);
  assert.deepEqual(pageErrors, [], `hash malformado provoca pageerror: ${pageErrors.join(' | ')}`);
  assert.equal(await page.locator('[data-fragment-link][data-current="true"]').count(), 0, 'hash malformado no debe seleccionar un fragmento');
  assert.equal(await page.locator('.excerpt-section').count(), 3, 'hash malformado no debe ocultar contenido');
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  assert.ok(overflow <= 1, `hash malformado genera overflow horizontal: ${overflow}px`);
  console.log('manecillas-fragments-hash-regression: OK');
} finally {
  await context.close();
  await browser.close();
}
