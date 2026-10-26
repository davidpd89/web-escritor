import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

try {
  for (const route of ['/eventos.html', '/ferias.html']) {
    for (const width of [320, 390, 768, 1440]) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: 'reduce' });
      const page = await context.newPage();
      try {
        const response = await page.goto(`${ORIGIN}${route}`, { waitUntil: 'load' });
        assert.ok(response?.ok(), `${route} ${width}px: navegación HTTP fallida`);
        const manifestHref = await page.locator('link[rel="manifest"]').getAttribute('href');
        assert.ok(manifestHref, `${route} ${width}px: falta enlace al manifiesto PWA`);
        const manifestResponse = await context.request.get(new URL(manifestHref, ORIGIN).href);
        assert.ok(manifestResponse.ok(), `${route}: manifiesto HTTP ${manifestResponse.status()}`);
        const manifest = await manifestResponse.json();
        const state = await page.evaluate(() => {
          const heading = document.querySelector('main h1');
          const rect = heading?.getBoundingClientRect();
          return {
            theme: document.querySelector('meta[name="theme-color"]')?.content,
            heading: heading?.textContent.trim(),
            headingRect: rect ? { left: rect.left, right: rect.right, width: rect.width, height: rect.height } : null,
            overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth
          };
        });
        assert.equal(state.theme?.toLowerCase(), manifest.theme_color?.toLowerCase(), `${route} ${width}px: theme-color ${state.theme} distinto del manifiesto ${manifest.theme_color}`);
        assert.ok(state.headingRect?.width > 0 && state.headingRect.height > 0, `${route} ${width}px: encabezado no visible (${state.heading})`);
        assert.ok(state.headingRect.left >= -1 && state.headingRect.right <= width + 1, `${route} ${width}px: encabezado fuera del viewport: ${JSON.stringify(state.headingRect)}`);
        assert.ok(state.overflow <= 1, `${route} ${width}px: desbordamiento horizontal de ${state.overflow}px`);
      } finally {
        await context.close();
      }
    }
  }
} finally {
  await browser.close();
}
console.log('OK: identidad visual PWA de Eventos y Ferias');
