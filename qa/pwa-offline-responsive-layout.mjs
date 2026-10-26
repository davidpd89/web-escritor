import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = (process.env.SITE_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const browser = await chromium.launch({ headless: true });

try {
  for (const width of [320, 375, 768, 1280]) {
    const page = await browser.newPage({ viewport: { width, height: 800 } });
    try {
      const response = await page.goto(`${base}/offline.html`, { waitUntil: 'load' });
      assert.equal(response?.status(), 200, `/offline.html ${width}px: HTTP inesperado`);
      await page.locator('#offline-title').waitFor({ state: 'visible' });
      const result = await page.evaluate(() => {
        const rect = el => {
          const r = el.getBoundingClientRect();
          return { left: r.left, right: r.right, width: r.width, height: r.height };
        };
        const selectors = ['main', '.offline-card', '#offline-title', '.lead', '.status', '.note'];
        const elements = selectors.map(selector => {
          const el = document.querySelector(selector);
          return { selector, ...rect(el), visibility: getComputedStyle(el).visibility };
        });
        const buttons = [...document.querySelectorAll('.actions button')].filter(el => getComputedStyle(el).display !== 'none').map(el => ({ text: el.textContent.trim(), ...rect(el) }));
        return { viewport: document.documentElement.clientWidth, scrollWidth: document.documentElement.scrollWidth, elements, buttons };
      });
      assert.ok(result.scrollWidth <= result.viewport + 1, `/offline.html ${width}px: scrollWidth=${result.scrollWidth}, viewport=${result.viewport}`);
      for (const el of result.elements) {
        assert.equal(el.visibility, 'visible', `/offline.html ${width}px: ${el.selector} invisible`);
        assert.ok(el.left >= -1 && el.right <= result.viewport + 1, `/offline.html ${width}px: ${el.selector} fuera del viewport: ${JSON.stringify(el)}`);
        assert.ok(el.width > 0 && el.height > 0, `/offline.html ${width}px: ${el.selector} sin caja visible`);
      }
      assert.ok(result.buttons.length >= 1, `/offline.html ${width}px: ninguna acción visible`);
      for (const button of result.buttons) {
        assert.ok(button.height >= 44, `/offline.html ${width}px: botón ${button.text} de ${button.height}px`);
        assert.ok(button.left >= -1 && button.right <= result.viewport + 1, `/offline.html ${width}px: botón ${button.text} recortado`);
      }
    } finally {
      await page.close();
    }
  }
} finally {
  await browser.close();
}
console.log('PASS PWA offline responsive layout');