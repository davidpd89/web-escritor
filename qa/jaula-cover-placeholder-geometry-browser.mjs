import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const ROUTE = '/donde-empieza-la-jaula/';
const browser = await chromium.launch({ headless: true });

try {
  for (const width of [320, 360, 390, 768, 1024, 1440]) {
    const context = await browser.newContext({ viewport: { width, height: 900 } });
    const page = await context.newPage();
    const response = await page.goto(`${ORIGIN}${ROUTE}`, { waitUntil: 'load' });
    assert.equal(response?.status(), 200, `${ROUTE} ${width}px: HTTP incorrecto`);
    await page.evaluate(() => document.fonts.ready);

    const result = await page.evaluate(() => {
      const fallback = document.querySelector('.book-cover-fallback');
      const zone = document.querySelector('.book-cover-zone');
      if (!fallback || !zone) throw new Error('Falta el marcador editorial');
      const r = fallback.getBoundingClientRect();
      const z = zone.getBoundingClientRect();
      const css = getComputedStyle(fallback);
      return {
        width: r.width,
        height: r.height,
        left: r.left,
        right: r.right,
        zoneLeft: z.left,
        zoneRight: z.right,
        visible: css.display !== 'none' && css.visibility !== 'hidden',
        brokenImages: [...document.images].filter(img => img.complete && img.naturalWidth === 0).map(img => img.currentSrc),
        overflow: document.documentElement.scrollWidth - innerWidth
      };
    });

    assert.ok(result.visible, `${ROUTE} ${width}px: marcador oculto`);
    assert.ok(result.width > 40 && result.height > 60, `${ROUTE} ${width}px: marcador ${result.width}x${result.height}`);
    assert.ok(Math.abs(result.height / result.width - 1.5) < 0.12, `${ROUTE} ${width}px: proporción ${result.height / result.width}`);
    assert.ok(result.left >= -1 && result.right <= width + 1, `${ROUTE} ${width}px: portada fuera del viewport`);
    assert.ok(result.left >= result.zoneLeft - 1 && result.right <= result.zoneRight + 1, `${ROUTE} ${width}px: portada desborda su contenedor`);
    assert.deepEqual(result.brokenImages, [], `${ROUTE} ${width}px: imágenes rotas`);
    assert.ok(result.overflow <= 1, `${ROUTE} ${width}px: overflow ${result.overflow}px`);
    await context.close();
  }
  console.log('OK jaula placeholder geometry');
} finally {
  await browser.close();
}
