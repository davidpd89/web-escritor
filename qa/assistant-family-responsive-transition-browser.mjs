import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const O = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await page.route('**/*', r => new URL(r.request().url()).origin === O ? r.continue() : r.abort());
  await page.goto(`${O}/autor.html`, { waitUntil: 'networkidle' });
  await page.locator('[data-assistant-search-open]').click();
  await page.locator('.assistant-widget__panel').waitFor({ state: 'visible' });
  const frame = page.frameLocator('.assistant-widget__frame');
  const query = frame.locator('[data-assistant-query]');
  const draft = '¿Qué herramientas gratuitas hay para escritores?';
  await query.fill(draft);
  for (const [width, height] of [[320, 568], [641, 800], [1024, 768], [844, 390], [390, 844]]) {
    await page.setViewportSize({ width, height });
    const rect = await page.locator('.assistant-widget__panel').evaluate(e => {
      const r = e.getBoundingClientRect();
      return { left: r.left, right: r.right, top: r.top, bottom: r.bottom };
    });
    assert.ok(rect.left >= -1 && rect.right <= width + 1, `${width}x${height}: horizontal clipping ${JSON.stringify(rect)}`);
    assert.ok(rect.top >= -1 && rect.bottom <= height + 1, `${width}x${height}: vertical clipping ${JSON.stringify(rect)}`);
    assert.equal(await query.inputValue(), draft, `${width}x${height}: lost draft`);
  }
  await frame.locator('[data-assistant-submit]').click();
  await frame.locator('.assistant-message--user').last().waitFor();
  assert.match(await frame.locator('.assistant-message--assistant').last().innerText(), /herramientas/i);
  assert.equal(await page.locator('.assistant-widget__panel').isVisible(), true);
} finally {
  await browser.close();
}
console.log('PASS assistant responsive state transitions');
