import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const browser = await chromium.launch({headless:true});
try {
  for (const route of ['/eventos.html', '/ferias.html']) {
    const context = await browser.newContext();
    try {
      const page = await context.newPage();
      const response = await page.goto(BASE + route, {waitUntil:'domcontentloaded'});
      assert.ok(response?.ok(), `${route}: documento inaccesible`);
      const href = await page.locator('link[rel="manifest"]').getAttribute('href');
      assert.ok(href, `${route}: falta manifest`);
      const url = new URL(href, BASE);
      assert.equal(url.origin, new URL(BASE).origin, `${route}: manifest externo`);
      const manifestResponse = await context.request.get(url.href);
      assert.ok(manifestResponse.ok(), `${route}: manifest HTTP ${manifestResponse.status()}`);
      const manifest = await manifestResponse.json();
      assert.equal(manifest.display, 'standalone', `${route}: display PWA`);
      assert.equal(manifest.lang, 'es', `${route}: idioma PWA`);
      assert.ok(manifest.name && manifest.start_url, `${route}: identidad PWA incompleta`);
      assert.ok(Array.isArray(manifest.icons) && manifest.icons.length, `${route}: iconos ausentes`);
      for (const icon of manifest.icons) {
        const iconUrl = new URL(icon.src, url);
        assert.equal(iconUrl.origin, url.origin, `${route}: icono externo ${icon.src}`);
        const result = await page.evaluate(async src => {
          const image = new Image();
          image.src = src;
          try { await image.decode(); return {width:image.naturalWidth,height:image.naturalHeight}; }
          catch { return null; }
        }, iconUrl.href);
        assert.ok(result, `${route}: icono no decodificable ${icon.src}`);
        const sizes = icon.sizes.split(/\s+/);
        assert.ok(sizes.includes(`${result.width}x${result.height}`), `${route}: ${icon.src} declara ${icon.sizes} pero mide ${result.width}x${result.height}`);
      }
    } finally { await context.close(); }
  }
} finally { await browser.close(); }
console.log('PASS Eventos/Ferias: manifest e iconos PWA');