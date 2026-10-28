import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  for (const route of ['/asistente/', '/asistente/embed.html']) {
    for (const width of [320, 390, 768, 1440]) {
      const page = await browser.newPage({ viewport: { width, height: 900 } });
      await page.goto(origin + route, { waitUntil: 'load' });
      const field = page.locator('[data-assistant-query]');
      await field.waitFor({ state: 'visible' });
      const metrics = await field.evaluate(el => {
        const s = getComputedStyle(el);
        return { font: parseFloat(s.fontSize), line: parseFloat(s.lineHeight), family: s.fontFamily, width: el.clientWidth, scrollWidth: el.scrollWidth };
      });
      assert.ok(metrics.font >= 16, `${route} ${width}px: textarea ${metrics.font}px, mínimo 16px`);
      assert.ok(metrics.line / metrics.font >= 1.3 && metrics.line / metrics.font <= 1.8, `${route} ${width}px: interlineado ${metrics.line / metrics.font}`);
      assert.ok(metrics.family.length > 0, `${route} ${width}px: familia tipográfica no resuelta`);
      assert.ok(metrics.scrollWidth <= metrics.width + 1, `${route} ${width}px: campo desbordado ${JSON.stringify(metrics)}`);
      await page.close();
    }
  }
} finally { await browser.close(); }
console.log('assistant-composer-typography-parity: OK');
