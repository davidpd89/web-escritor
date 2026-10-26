import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

try {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const page = await context.newPage();
  try {
    for (const route of ['/eventos.html', '/ferias.html']) {
      const response = await page.goto(`${ORIGIN}${route}`, { waitUntil: 'load' });
      assert.ok(response?.ok(), `${route}: página no disponible`);
      const manifestHref = await page.locator('link[rel="manifest"]').getAttribute('href');
      assert.ok(manifestHref, `${route}: manifiesto ausente`);
      const manifestResponse = await context.request.get(new URL(manifestHref, ORIGIN).href);
      assert.ok(manifestResponse.ok(), `${route}: manifiesto HTTP ${manifestResponse.status()}`);
      const manifest = await manifestResponse.json();
      assert.ok(Array.isArray(manifest.icons) && manifest.icons.length > 0, `${route}: manifiesto sin iconos`);
      const icons = manifest.icons.map(icon => ({ src: icon.src, sizes: icon.sizes, purpose: icon.purpose || 'any' }));
      const documentIcons = await page.locator('link[rel="icon"], link[rel="apple-touch-icon"]').evaluateAll(nodes => nodes.map(node => ({ src: node.getAttribute('href'), sizes: node.getAttribute('sizes') })));
      assert.ok(documentIcons.length > 0, `${route}: documento sin iconos`);
      for (const icon of [...icons, ...documentIcons]) {
        const url = new URL(icon.src, ORIGIN);
        assert.equal(url.origin, ORIGIN, `${route}: icono fuera del origen ${icon.src}`);
        const resource = await context.request.get(url.href);
        assert.ok(resource.ok(), `${route}: icono ${icon.src} devuelve HTTP ${resource.status()}`);
        const dimensions = await page.evaluate(async src => {
          const img = new Image();
          img.src = src;
          try { await img.decode(); return { width: img.naturalWidth, height: img.naturalHeight }; }
          catch { return { width: 0, height: 0 }; }
        }, url.href);
        assert.ok(dimensions.width > 0 && dimensions.height > 0, `${route}: icono ${icon.src} no decodificable`);
        if (icon.sizes && icon.sizes !== 'any') {
          const declared = icon.sizes.split(/\s+/).map(size => size.split('x').map(Number));
          assert.ok(declared.some(([w, h]) => w === dimensions.width && h === dimensions.height), `${route}: icono ${icon.src} declara ${icon.sizes} pero mide ${dimensions.width}x${dimensions.height}`);
        }
      }
    }
  } finally {
    await context.close();
  }
} finally {
  await browser.close();
}
console.log('OK: iconos PWA de Eventos y Ferias');
