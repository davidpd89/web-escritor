import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const routes = ['/editoriales/suma-de-letras/', '/mapa-del-sitio/'];
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

try {
  for (const width of [320, 360, 390]) {
    const context = await browser.newContext({ viewport: { width, height: 800 }, isMobile: true, hasTouch: true });
    const page = await context.newPage();
    for (const route of routes) {
      const response = await page.goto(new URL(route, BASE).href, { waitUntil: 'domcontentloaded' });
      assert.ok(response?.ok(), `${route} ${width}px: respuesta HTTP ${response?.status()}`);
      const links = await page.locator('a[href][target="_blank"]').evaluateAll(nodes => nodes.filter(a => a.getClientRects().length).map(a => ({ href: a.href, rel: a.rel, text: a.getAttribute('aria-label') || a.textContent.trim() })));
      assert.ok(links.length > 0, `${route} ${width}px: no se han encontrado enlaces externos para verificar`);
      for (const link of links) {
        const url = new URL(link.href);
        if (url.origin === new URL(BASE).origin) continue;
        assert.equal(url.protocol, 'https:', `${route} ${width}px: enlace externo no HTTPS: ${link.href}`);
        assert.match(link.rel, /(?:^|\s)(?:noopener|noreferrer)(?:\s|$)/i, `${route} ${width}px: enlace ${link.href} sin aislamiento de ventana`);
        assert.ok(link.text, `${route} ${width}px: enlace ${link.href} sin nombre accesible básico`);
      }
    }
    await context.close();
  }
} finally {
  await browser.close();
}
console.log('PASS postmerge mobile external isolation');
