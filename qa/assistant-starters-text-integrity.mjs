import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  for (const route of ['/asistente/', '/asistente/embed.html']) {
    for (const width of [320, 390, 768]) {
      const page = await browser.newPage({ viewport: { width, height: 900 } });
      await page.goto(origin + route, { waitUntil: 'load' });
      const buttons = page.locator('[data-assistant-example]:visible');
      await buttons.first().waitFor({ state: 'visible' });
      const values = await buttons.evaluateAll(els => els.map(el => {
        const s = getComputedStyle(el);
        const r = el.getBoundingClientRect();
        const range = document.createRange();
        range.selectNodeContents(el);
        const textRect = range.getBoundingClientRect();
        return { text: el.textContent.trim(), font: parseFloat(s.fontSize), overflowX: el.scrollWidth - el.clientWidth, overflowY: el.scrollHeight - el.clientHeight, textBottom: textRect.bottom, bottom: r.bottom };
      }));
      assert.ok(values.length > 0, `${route} ${width}px: no hay preguntas sugeridas visibles`);
      for (const v of values) {
        assert.ok(v.font >= 12, `${route} ${width}px: texto demasiado pequeño en ${v.text}: ${v.font}px`);
        assert.ok(v.overflowX <= 1 && v.overflowY <= 1, `${route} ${width}px: desbordamiento en ${v.text}: ${JSON.stringify(v)}`);
        assert.ok(v.textBottom <= v.bottom + 1, `${route} ${width}px: texto cortado verticalmente en ${v.text}`);
      }
      await page.close();
    }
  }
} finally { await browser.close(); }
console.log('assistant-starters-text-integrity: OK');
