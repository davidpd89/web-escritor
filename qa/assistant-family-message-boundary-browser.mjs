import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const O = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  await page.route('**/*', r => new URL(r.request().url()).origin === O ? r.continue() : r.abort());
  await page.goto(`${O}/autor.html`, { waitUntil: 'networkidle' });
  await page.locator('[data-assistant-search-open]').click();
  const panel = page.locator('.assistant-widget__panel');
  await panel.waitFor({ state: 'visible' });
  const real = page.frameLocator('.assistant-widget__frame');
  await real.locator('[data-assistant-query]').waitFor();
  await page.evaluate(() => {
    const f = document.createElement('iframe');
    f.id = 'assistant-rogue-frame';
    f.src = '/asistente/embed.html';
    document.body.append(f);
  });
  const rogue = page.frameLocator('#assistant-rogue-frame');
  await rogue.locator('[data-assistant-query]').waitFor();
  await rogue.locator('body').evaluate(() => parent.postMessage({ type: 'assistant:close' }, location.origin));
  await page.waitForTimeout(100);
  assert.equal(await panel.isVisible(), true, 'same-origin sibling frame closed the widget');
  await page.evaluate(() => window.postMessage({ type: 'assistant:close' }, location.origin));
  await page.waitForTimeout(100);
  assert.equal(await panel.isVisible(), true, 'parent-window spoof closed the widget');
  await real.locator('[data-assistant-query]').press('Escape');
  await panel.waitFor({ state: 'hidden' });
  assert.equal(await page.locator('.assistant-widget__launcher').getAttribute('aria-expanded'), 'false');
  assert.equal(await page.locator('.assistant-widget__launcher').evaluate(e => document.activeElement === e), true);
  await page.close();
} finally {
  await browser.close();
}
console.log('PASS assistant frame message boundary');
