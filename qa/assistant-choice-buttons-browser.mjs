import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  await page.route('**/*', r => new URL(r.request().url()).origin === origin ? r.continue() : r.abort());
  await page.goto(`${origin}/asistente/`);
  await page.locator('[data-assistant-query]').fill('Quiero leer un fragmento');
  await page.locator('[data-assistant-submit]').click();
  await page.locator('.assistant-reply-chip').first().waitFor();
  const options = page.locator('.assistant-reply-chip');
  assert.equal(await options.count(), 2);
  const chosen = await options.first().innerText();
  assert.match(chosen, /manecillas/i);
  await options.first().click();
  await page.waitForFunction(() => document.querySelector('[data-assistant-form]')?.getAttribute('aria-busy') === 'false');
  assert.equal(await page.locator('.assistant-message--user').count(), 2);
  const answer = page.locator('.assistant-message--assistant').last();
  const hrefs = await answer.locator('.assistant-message__sources a').evaluateAll(
    els => els.map(el => el.getAttribute('href'))
  );
  assert.deepEqual(hrefs, ['/las-manecillas-del-recuerdo/fragmentos/']);
  assert.equal(await page.locator('[data-assistant-query]').inputValue(), '');
} finally { await browser.close(); }
console.log('assistant-choice-buttons: OK');
