import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
try {
  for (const [width, height] of [[320, 568], [360, 640], [390, 844], [1366, 768]]) {
    const page = await browser.newPage({ viewport: { width, height }, reducedMotion: 'reduce' });
    await page.route('**/*', r => new URL(r.request().url()).origin === origin ? r.continue() : r.abort());
    await page.goto(origin + '/autor.html');
    await page.locator('.assistant-widget__launcher').click();
    await page.locator('.assistant-widget__panel').waitFor({ state: 'visible' });
    const panel = await page.locator('.assistant-widget__panel').boundingBox();
    assert(panel && panel.x >= -1 && panel.y >= -1 && panel.x + panel.width <= width + 1 && panel.y + panel.height <= height + 1,
      `Panel fuera del viewport ${width}x${height}: ${JSON.stringify(panel)}`);
    const frame = page.frameLocator('.assistant-widget__frame');
    const send = frame.locator('[data-assistant-submit]');
    await send.waitFor();
    const hit = await send.evaluate(el => {
      const r = el.getBoundingClientRect();
      const target = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
      return { width: r.width, height: r.height, hit: target === el || el.contains(target) };
    });
    assert(hit.hit, `Botón de envío tapado: ${width}x${height}`);
    assert(hit.width >= 38 && hit.height >= 38, `Objetivo demasiado pequeño: ${width}x${height}`);
    await page.close();
  }
} finally { await browser.close(); }
console.log('assistant-widget-hit-testing: OK');
