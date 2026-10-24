import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const O = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const browser = await chromium.launch({ headless: true });
async function verify(scope, selector, label) {
  const target = scope.locator(selector).first();
  await target.scrollIntoViewIfNeeded();
  const result = await target.evaluate(el => {
    const r = el.getBoundingClientRect();
    const x = r.left + r.width / 2;
    const y = r.top + r.height / 2;
    const hit = document.elementFromPoint(x, y);
    return { width: r.width, height: r.height, inside: x >= 0 && y >= 0 && x < innerWidth && y < innerHeight, hit: Boolean(hit && (hit === el || el.contains(hit))) };
  });
  assert.ok(result.width >= 24 && result.height >= 24, `${label}: collapsed target`);
  assert.ok(result.inside && result.hit, `${label}: occluded or offscreen ${JSON.stringify(result)}`);
}
try {
  for (const [width, height] of [[320, 568], [390, 640], [844, 390]]) {
    const page = await browser.newPage({ viewport: { width, height } });
    await page.route('**/*', r => new URL(r.request().url()).origin === O ? r.continue() : r.abort());
    await page.goto(`${O}/asistente/`, { waitUntil: 'load' });
    await page.locator('[data-assistant-log]').waitFor();
    for (const selector of ['[data-assistant-query]', '[data-assistant-submit]', '[data-assistant-example]']) await verify(page, selector, `standalone ${width}x${height} ${selector}`);
    await page.goto(`${O}/autor.html`, { waitUntil: 'networkidle' });
    await page.locator('[data-assistant-search-open]').click();
    await page.locator('.assistant-widget__panel').waitFor({ state: 'visible' });
    const frame = page.frameLocator('.assistant-widget__frame');
    for (const selector of ['[data-assistant-query]', '[data-assistant-submit]', '[data-assistant-example]']) await verify(frame, selector, `embed ${width}x${height} ${selector}`);
    await page.close();
  }
} finally {
  await browser.close();
}
console.log('PASS assistant hit testing');
