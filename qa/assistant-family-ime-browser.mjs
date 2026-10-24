import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const O = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  await page.route('**/*', r => new URL(r.request().url()).origin === O ? r.continue() : r.abort());
  await page.goto(`${O}/asistente/`, { waitUntil: 'load' });
  const query = page.locator('[data-assistant-query]');
  await query.fill('¿Qué herramientas');
  await query.evaluate(el => el.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true, isComposing: true })));
  assert.equal(await page.locator('.assistant-message--user').count(), 0, 'IME Enter submitted prematurely');
  await query.press('Shift+Enter');
  await query.type('gratuitas hay para escritores?');
  assert.match(await query.inputValue(), /\n/, 'Shift+Enter did not insert a newline');
  assert.equal(await page.locator('.assistant-message--user').count(), 0);
  await query.press('Enter');
  await page.waitForFunction(() => document.querySelector('[data-assistant-form]')?.getAttribute('aria-busy') === 'false');
  assert.equal(await page.locator('.assistant-message--user').count(), 1);
  assert.equal(await page.locator('.assistant-message--assistant').count(), 2);
  const text = await page.locator('.assistant-message--user').last().innerText();
  assert.match(text, /herramientas gratuitas hay para escritores/i);
} finally {
  await browser.close();
}
console.log('PASS assistant IME and multiline input');
