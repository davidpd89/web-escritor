import { chromium } from 'playwright';
import assert from 'node:assert/strict';

const base = (process.env.BASE_URL || process.env.SITE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const browser = await chromium.launch({ headless: true });
try {
  for (const width of [320, 360, 390]) {
    const page = await browser.newPage({ viewport: { width, height: 780 } });
    try {
      await page.goto(`${base}/redes-sociales/`, { waitUntil: 'domcontentloaded' });
      await page.locator('#social-grid .social-card').first().waitFor({ state: 'visible' });
      const result = await page.evaluate(() => {
        const viewport = document.documentElement.clientWidth;
        const cards = [...document.querySelectorAll('#social-grid .social-card')];
        const failures = [];
        for (const card of cards) {
          const id = card.dataset.network;
          for (const element of [card, ...card.querySelectorAll('a, [data-role="count"], [data-role="meta"]')]) {
            const rect = element.getBoundingClientRect();
            if (rect.width > 0 && (rect.left < -1 || rect.right > viewport + 1)) {
              failures.push(`${id}: ${element.tagName} [${rect.left}, ${rect.right}]`);
            }
          }
        }
        return { viewport, scrollWidth: document.documentElement.scrollWidth, count: cards.length, failures };
      });
      assert.equal(result.count, 6, `redes-sociales ${width}px: número de tarjetas`);
      assert.ok(result.scrollWidth <= result.viewport + 1, `redes-sociales ${width}px: scrollWidth=${result.scrollWidth}, viewport=${result.viewport}`);
      assert.deepEqual(result.failures, [], `redes-sociales ${width}px: elementos desbordados`);
    } finally {
      await page.close();
    }
  }
} finally {
  await browser.close();
}
