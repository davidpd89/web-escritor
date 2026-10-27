import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
const sizes = [[320, 640], [360, 740], [390, 844], [768, 1024], [1280, 900]];

try {
  for (const [width, height] of sizes) {
    const context = await browser.newContext({ viewport: { width, height }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    await page.goto(`${origin}/autor.html`, { waitUntil: 'networkidle' });
    await page.locator('[data-assistant-search-open]').click();
    const panel = page.locator('.assistant-widget__panel');
    await panel.waitFor({ state: 'visible' });
    const panelBox = await panel.boundingBox();
    assert(panelBox, `${width}x${height}: panel sin caja`);
    assert(panelBox.x >= -1 && panelBox.y >= -1 && panelBox.x + panelBox.width <= width + 1 && panelBox.y + panelBox.height <= height + 1, `${width}x${height}: panel fuera del viewport: ${JSON.stringify(panelBox)}`);
    const frame = page.frameLocator('.assistant-widget__frame');
    await frame.locator('[data-assistant-query]').waitFor({ state: 'visible' });
    const geometry = await frame.locator('.assistant-chat').evaluate(chat => {
      const rect = selector => {
        const r = document.querySelector(selector).getBoundingClientRect();
        return { x: r.x, y: r.y, right: r.right, bottom: r.bottom, width: r.width, height: r.height };
      };
      return { query: rect('[data-assistant-query]'), send: rect('[data-assistant-submit]'), viewport: { width: innerWidth, height: innerHeight } };
    });
    for (const [name, rect] of [['query', geometry.query], ['send', geometry.send]]) {
      assert(rect.width > 0 && rect.height > 0, `${width}x${height}: ${name} sin dimensiones`);
      assert(rect.x >= -1 && rect.y >= -1 && rect.right <= geometry.viewport.width + 1 && rect.bottom <= geometry.viewport.height + 1, `${width}x${height}: ${name} recortado: ${JSON.stringify(rect)}`);
    }
    assert(geometry.query.right <= geometry.send.x + 1 || geometry.send.right <= geometry.query.x + 1 || geometry.query.bottom <= geometry.send.y + 1, `${width}x${height}: campo y botón se solapan`);
    await context.close();
  }
} finally {
  await browser.close();
}
console.log('assistant-widget-composer-geometry: OK');