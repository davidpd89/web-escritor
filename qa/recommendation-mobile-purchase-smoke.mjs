import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.RECOMMENDATIONS_BASE_URL || 'http://127.0.0.1:4173';
const route = '/recomendaciones/libros/coraline/';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

try {
  for (const width of [320, 360, 390]) {
    const context = await browser.newContext({ viewport: { width, height: 850 }, reducedMotion: 'reduce', serviceWorkers: 'block' });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    const response = await page.goto(`${BASE}${route}`, { waitUntil: 'domcontentloaded' });
    assert(response?.ok(), `${route} @ ${width}px: HTTP ${response?.status()}`);
    await page.locator('main h1').waitFor({ state: 'visible' });
    assert.equal((await page.locator('main h1').innerText()).trim(), 'Coraline', `${route} @ ${width}px: título incorrecto`);
    await page.locator('.catalogue-book-cover').scrollIntoViewIfNeeded();
    const cover = await page.locator('.catalogue-book-cover').evaluate(img => ({ complete: img.complete, naturalWidth: img.naturalWidth, rect: img.getBoundingClientRect().toJSON() }));
    assert(cover.complete && cover.naturalWidth > 0, `${route} @ ${width}px: portada no cargada`);
    assert(cover.rect.left >= -1 && cover.rect.right <= width + 1, `${route} @ ${width}px: portada cortada`);
    const purchases = page.locator('main a[data-purchase-format]:visible');
    assert(await purchases.count() > 0, `${route} @ ${width}px: faltan opciones de compra`);
    for (let i = 0; i < await purchases.count(); i++) {
      const link = purchases.nth(i);
      await link.scrollIntoViewIfNeeded();
      const state = await link.evaluate(el => {
        const r = el.getBoundingClientRect();
        return { width: r.width, height: r.height, left: r.left, right: r.right, href: el.getAttribute('href') };
      });
      assert(state.href, `${route} @ ${width}px: compra ${i} sin destino`);
      assert(state.width >= 24 && state.height >= 24, `${route} @ ${width}px: compra ${i} demasiado pequeña: ${JSON.stringify(state)}`);
      assert(state.left >= -1 && state.right <= width + 1, `${route} @ ${width}px: compra ${i} cortada: ${JSON.stringify(state)}`);
    }
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
    assert(overflow <= 1, `${route} @ ${width}px: desbordamiento horizontal ${overflow}px`);
    assert.deepEqual(errors, [], `${route} @ ${width}px: errores JavaScript`);
    await context.close();
  }
} finally {
  await browser.close();
}
