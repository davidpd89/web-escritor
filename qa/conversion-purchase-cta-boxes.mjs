import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:8000';
const browser = await chromium.launch({ headless: true });
const routes = ['/las-manecillas-del-recuerdo/', '/las-manecillas-del-recuerdo/kindle/'];

try {
  for (const width of [320, 375, 768, 1280]) {
    const page = await browser.newPage({ viewport: { width, height: 900 } });
    for (const route of routes) {
      const response = await page.goto(new URL(route, origin).href, { waitUntil: 'load' });
      assert.ok(response?.ok(), `${route}: HTTP ${response?.status()}`);
      const links = page.locator('.book-actions a[href]');
      assert.ok(await links.count() > 0, `${route}: no hay enlaces en book-actions`);
      let checked = 0;
      for (const link of await links.all()) {
        if (!await link.isVisible()) continue;
        const result = await link.evaluate(el => {
          const r = el.getBoundingClientRect();
          const s = getComputedStyle(el);
          return { x: r.x, right: r.right, width: r.width, height: r.height, visibility: s.visibility, opacity: Number(s.opacity), fontSize: parseFloat(s.fontSize), text: el.innerText.trim() };
        });
        assert.ok(result.width > 0 && result.height > 0, `${route} @${width}: caja vacía ${JSON.stringify(result)}`);
        assert.ok(result.x >= -1 && result.right <= width + 1, `${route} @${width}: CTA fuera del viewport ${JSON.stringify(result)}`);
        assert.ok(result.visibility === 'visible' && result.opacity > 0, `${route} @${width}: CTA oculto ${JSON.stringify(result)}`);
        assert.ok(result.fontSize >= 12 && result.text.length > 0, `${route} @${width}: texto ilegible ${JSON.stringify(result)}`);
        checked++;
      }
      assert.ok(checked > 0, `${route} @${width}: ningún CTA comercial visible`);
    }
    await page.close();
  }
} finally {
  await browser.close();
}
console.log('conversion-purchase-cta-boxes: OK');