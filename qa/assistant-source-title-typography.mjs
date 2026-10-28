import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  for (const width of [320, 390, 768, 1440]) {
    const page = await browser.newPage({ viewport: { width, height: 900 } });
    await page.goto(`${origin}/asistente/`, { waitUntil: 'load' });
    await page.locator('[data-assistant-query]').fill('¿De qué trata Las manecillas del recuerdo?');
    await page.locator('[data-assistant-submit]').click();
    await page.waitForFunction(() => document.querySelector('[data-assistant-form]')?.getAttribute('aria-busy') !== 'true');
    const titles = page.locator('[data-assistant-log] .assistant-source__title:visible');
    await titles.first().waitFor({ state: 'visible' });
    const results = await titles.evaluateAll(els => els.map(el => {
      const s = getComputedStyle(el);
      return { text: el.textContent.trim(), font: parseFloat(s.fontSize), whiteSpace: s.whiteSpace, overflow: s.overflow, ellipsis: s.textOverflow, clipped: el.scrollWidth > el.clientWidth + 1 };
    }));
    for (const r of results) {
      assert.ok(r.text.length > 0, `/asistente/ ${width}px: título documental vacío`);
      assert.ok(r.font >= 12, `/asistente/ ${width}px: fuente documental ${r.text} con ${r.font}px`);
      assert.notEqual(r.ellipsis, 'ellipsis', `/asistente/ ${width}px: título truncado ${r.text}`);
      assert.notEqual(r.whiteSpace, 'nowrap', `/asistente/ ${width}px: título sin ajuste de línea ${r.text}`);
      assert.ok(!r.clipped, `/asistente/ ${width}px: título documental recortado ${r.text}`);
    }
    await page.close();
  }
} finally { await browser.close(); }
console.log('assistant-source-title-typography: OK');
