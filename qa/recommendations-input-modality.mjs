import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.RECOMMENDATIONS_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch();
const cases = ['fantasía', 'niñez', 'año', 'Coraline', 'magia'];
const failures = [];
try {
  const context = await browser.newContext();
  await context.route('**/*', route => new URL(route.request().url()).origin === new URL(BASE).origin ? route.continue() : route.abort());
  const page = await context.newPage();
  await page.goto(BASE + '/recomendaciones/');
  const field = page.locator('[data-filter="q"]');
  assert.equal(await field.count(), 1);
  const snapshot = () => page.locator('[data-catalogue-book]:not([hidden])').evaluateAll(nodes => nodes.map(n => n.dataset.bookId));
  for (const query of cases) {
    await field.fill(query);
    await field.dispatchEvent('input');
    const direct = await snapshot();
    await field.fill('');
    await field.evaluate((el, text) => {
      el.dispatchEvent(new CompositionEvent('compositionstart', { bubbles: true, data: '' }));
      el.value = text;
      el.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertCompositionText', data: text, isComposing: true }));
      el.dispatchEvent(new CompositionEvent('compositionend', { bubbles: true, data: text }));
      el.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: text }));
    }, query);
    const composed = await snapshot();
    if (JSON.stringify(direct) !== JSON.stringify(composed)) failures.push(`${query}: entrada directa e IME difieren`);
    await field.fill('');
    await field.evaluate((el, text) => {
      el.value = text;
      el.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertFromPaste', data: text }));
    }, query);
    const pasted = await snapshot();
    if (JSON.stringify(direct) !== JSON.stringify(pasted)) failures.push(`${query}: entrada directa y pegado difieren`);
  }
  assert.deepEqual(failures, []);
  await context.close();
} finally {
  await browser.close();
}
console.log('OK: equivalencia de modalidades de entrada');