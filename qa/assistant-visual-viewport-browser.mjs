import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

try {
  for (const height of [844, 568, 420]) {
    const context = await browser.newContext({ viewport: { width: 390, height }, isMobile: true, hasTouch: true, reducedMotion: 'reduce' });
    const page = await context.newPage();
    await page.goto(`${origin}/asistente/embed.html`, { waitUntil: 'networkidle' });
    const query = page.locator('[data-assistant-query]');
    await query.waitFor({ state: 'visible' });
    await query.focus();
    const result = await page.evaluate(() => {
      const viewport = window.visualViewport;
      const controls = ['[data-assistant-query]', '[data-assistant-submit]'];
      return controls.map(selector => {
        const element = document.querySelector(selector);
        const r = element.getBoundingClientRect();
        return { selector, top: r.top, bottom: r.bottom, left: r.left, right: r.right, visibleBottom: viewport.offsetTop + viewport.height, visibleRight: viewport.offsetLeft + viewport.width };
      });
    });
    for (const r of result) {
      assert(r.top >= -1 && r.bottom <= r.visibleBottom + 1, `embed.html ${height}px: ${r.selector} fuera del viewport visual vertical: ${JSON.stringify(r)}`);
      assert(r.left >= -1 && r.right <= r.visibleRight + 1, `embed.html ${height}px: ${r.selector} fuera del viewport visual horizontal: ${JSON.stringify(r)}`);
    }
    await context.close();
  }
} finally {
  await browser.close();
}
console.log('assistant-visual-viewport: OK');