import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  for (const width of [320, 390, 768, 1440]) {
    const page = await browser.newPage({ viewport: { width, height: 900 } });
    await page.goto(`${origin}/asistente/`, { waitUntil: 'load' });
    const paragraph = page.locator('[data-assistant-log] .assistant-message__bubble p').first();
    await paragraph.waitFor({ state: 'visible' });
    const metrics = await paragraph.evaluate(el => {
      const s = getComputedStyle(el);
      const r = el.getBoundingClientRect();
      return { font: parseFloat(s.fontSize), line: parseFloat(s.lineHeight), width: r.width, parentWidth: el.parentElement.clientWidth, clipped: el.scrollWidth > el.clientWidth + 1 };
    });
    assert.ok(metrics.font >= 16, `/asistente/ ${width}px: fuente ${metrics.font}px inferior a 16px`);
    assert.ok(metrics.line / metrics.font >= 1.4 && metrics.line / metrics.font <= 1.9, `/asistente/ ${width}px: interlineado ${metrics.line / metrics.font}`);
    assert.ok(metrics.width <= metrics.parentWidth + 1 && !metrics.clipped, `/asistente/ ${width}px: párrafo recortado ${JSON.stringify(metrics)}`);
    await page.close();
  }
} finally { await browser.close(); }
console.log('assistant-message-typography-regression: OK');
