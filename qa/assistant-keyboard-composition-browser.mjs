import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  await page.route('**/*', r => new URL(r.request().url()).origin === origin ? r.continue() : r.abort());
  await page.goto(`${origin}/asistente/`);
  const input = page.locator('[data-assistant-query]');
  await input.fill('primera línea');
  await input.press('Shift+Enter');
  await input.type('segunda línea');
  assert.match(await input.inputValue(), /primera línea\nsegunda línea/);
  assert.equal(await page.locator('.assistant-message--user').count(), 0);

  await input.fill('¿Qué es Noveris?');
  await input.dispatchEvent('keydown', { key: 'Enter', code: 'Enter', isComposing: true, bubbles: true, cancelable: true });
  assert.equal(await page.locator('.assistant-message--user').count(), 0, 'IME provocó envío');
  assert.equal(await input.inputValue(), '¿Qué es Noveris?');

  await input.press('Enter');
  await page.waitForFunction(() => document.querySelector('[data-assistant-form]')?.getAttribute('aria-busy') === 'false');
  assert.equal(await page.locator('.assistant-message--user').count(), 1);
  assert.equal(await input.inputValue(), '');
  assert.equal(await input.evaluate(el => el === document.activeElement), true);
} finally { await browser.close(); }
console.log('assistant-keyboard-composition: OK');
