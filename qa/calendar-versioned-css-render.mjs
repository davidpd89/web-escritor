import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

try {
  for (const route of ['/eventos.html', '/ferias.html']) {
    for (const width of [390, 1440]) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: 'reduce' });
      const page = await context.newPage();
      try {
        const response = await page.goto(`${ORIGIN}${route}`, { waitUntil: 'load' });
        assert.ok(response?.ok(), `${route} ${width}px: HTML no disponible`);
        const styles = await page.locator('link[rel="stylesheet"][href*="?v="]').evaluateAll(nodes => nodes.map(node => node.getAttribute('href')));
        assert.ok(styles.length > 0, `${route}: no se han encontrado CSS versionados`);
        for (const href of styles) {
          const resource = await context.request.get(new URL(href, ORIGIN).href);
          assert.ok(resource.ok(), `${route}: CSS ${href} devuelve HTTP ${resource.status()}`);
          assert.match(resource.headers()['content-type'] || '', /^text\/css\b/i, `${route}: CSS ${href} tiene MIME incorrecto`);
          assert.ok((await resource.body()).length > 0, `${route}: CSS ${href} está vacío`);
        }
        await page.evaluate(() => document.fonts?.ready);
        const state = await page.evaluate(() => {
          const h1 = document.querySelector('main h1');
          const main = document.querySelector('main');
          const h = h1 && getComputedStyle(h1);
          const r = h1?.getBoundingClientRect();
          return { fontSize: h ? parseFloat(h.fontSize) : 0, display: h?.display, width: r?.width || 0, height: r?.height || 0, mainWidth: main?.getBoundingClientRect().width || 0, overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth };
        });
        assert.ok(state.fontSize >= 16, `${route} ${width}px: tamaño H1 ${state.fontSize}px`);
        assert.notEqual(state.display, 'none', `${route} ${width}px: H1 oculto`);
        assert.ok(state.width > 0 && state.height > 0 && state.mainWidth > 0, `${route} ${width}px: cajas principales sin dimensiones: ${JSON.stringify(state)}`);
        assert.ok(state.overflow <= 1, `${route} ${width}px: overflow ${state.overflow}px`);
      } finally {
        await context.close();
      }
    }
  }
} finally {
  await browser.close();
}
console.log('OK: CSS versionados y presentación de calendarios');
