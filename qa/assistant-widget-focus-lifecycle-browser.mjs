import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  await page.route('**/*', r => new URL(r.request().url()).origin === origin ? r.continue() : r.abort());
  await page.goto(origin + '/autor.html');
  await page.locator('[data-assistant-search-open]').click();
  const launcher = page.locator('.assistant-widget__launcher');
  const panel = page.locator('.assistant-widget__panel');
  await panel.waitFor({ state: 'visible' });
  assert.equal(await launcher.getAttribute('aria-expanded'), 'true');
  const iframe = page.frameLocator('.assistant-widget__frame');
  await iframe.locator('[data-assistant-query]').waitFor();
  await page.locator('.assistant-widget__header button').click();
  assert.equal(await launcher.getAttribute('aria-expanded'), 'false');
  assert.equal(await panel.isVisible(), false);
  assert.equal(await launcher.evaluate(el => el === document.activeElement), true);

  await launcher.click();
  assert.equal(await panel.isVisible(), true);
  await iframe.locator('[data-assistant-query]').focus();
  await iframe.locator('[data-assistant-query]').press('Escape');
  await page.waitForFunction(() => document.querySelector('.assistant-widget__launcher')?.getAttribute('aria-expanded') === 'false');
  assert.equal(await panel.isVisible(), false);
} finally { await browser.close(); }
console.log('assistant-widget-focus-lifecycle: OK');
