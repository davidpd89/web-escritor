import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const O = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  await page.route('**/*', r => new URL(r.request().url()).origin === new URL(O).origin ? r.continue() : r.abort());
  await page.goto(O + '/editoriales/', { waitUntil: 'domcontentloaded' });
  const total = await page.locator('[data-editorial-card]').count();
  assert.ok(total > 50);
  await page.locator('[data-editoriales-status]').selectOption('open');
  await page.locator('[data-editoriales-country]').selectOption('España');
  await page.locator('[data-editoriales-direct]').check();
  const result = await page.evaluate(() => {
    const cards = [...document.querySelectorAll('[data-editorial-card]')];
    const eligible = cards.filter(c => c.dataset.status === 'open' && c.dataset.country === 'España' && c.dataset.direct === 'true');
    const visible = cards.filter(c => !c.hidden);
    return {
      expected: eligible.length,
      actual: visible.length,
      valid: visible.every(c => eligible.includes(c)),
      count: document.querySelector('[data-editoriales-count]').textContent,
      params: Object.fromEntries(new URLSearchParams(location.hash.slice(1)))
    };
  });
  assert.ok(result.expected > 0);
  assert.equal(result.actual, result.expected);
  assert.equal(result.valid, true);
  assert.equal(parseInt(result.count, 10), result.expected);
  assert.equal(result.params.estado, 'open');
  assert.equal(result.params.pais, 'España');
  assert.equal(result.params.directo, '1');
  await page.locator('[data-editoriales-reset]').click();
  assert.equal(await page.locator('[data-editorial-card]:not([hidden])').count(), total);
  assert.equal(await page.evaluate(() => document.activeElement?.matches('[data-editoriales-search]')), true);
} finally {
  await browser.close();
}
console.log('PASS: intersección, contador, URL y reset de editoriales');
