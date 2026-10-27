import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
try {
  for (const width of [360, 390, 768, 1280]) {
    const context = await browser.newContext({ javaScriptEnabled: false, viewport: { width, height: 844 } });
    const page = await context.newPage();
    try {
      const response = await page.goto(`${ORIGIN}/recomendaciones/`, { waitUntil: 'domcontentloaded' });
      assert.ok(response?.ok(), `/recomendaciones/ ${width}px: respuesta HTTP inválida`);
      const cards = page.locator('main[data-reading-catalogue] .catalogue-card');
      const count = await cards.count();
      assert.ok(count > 0, `/recomendaciones/ ${width}px: ninguna tarjeta prerenderizada`);
      for (const card of await cards.all()) {
        const result = await card.evaluate(el => {
          const rect = el.getBoundingClientRect();
          const style = getComputedStyle(el);
          const link = el.querySelector('h3 a[href]');
          return { width: rect.width, height: rect.height, display: style.display, visibility: style.visibility, href: link?.getAttribute('href'), text: link?.textContent?.trim() };
        });
        assert.ok(result.width > 0 && result.height > 0 && result.display !== 'none' && result.visibility !== 'hidden', `/recomendaciones/ ${width}px: tarjeta sin caja visible: ${JSON.stringify(result)}`);
        assert.ok(result.href?.startsWith('/recomendaciones/libros/') && result.text, `/recomendaciones/ ${width}px: tarjeta sin enlace o texto navegable: ${JSON.stringify(result)}`);
      }
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      assert.ok(overflow <= 2, `/recomendaciones/ ${width}px: desbordamiento horizontal de ${overflow}px`);
    } finally {
      await context.close();
    }
  }
} finally {
  await browser.close();
}
console.log('recommendations-nojs-card-visibility: PASS');
