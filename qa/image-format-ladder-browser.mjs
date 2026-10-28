// Verifica en un navegador real (Chromium, con soporte AVIF) que la
// cubierta de Manecillas en Home carga efectivamente el AVIF, no el WebP,
// y que las dimensiones renderizadas no cambian (L.1, 2026-08-23).
import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const MIME = new Map([
  ['.html', 'text/html; charset=utf-8'], ['.css', 'text/css; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'], ['.mjs', 'text/javascript; charset=utf-8'],
  ['.webp', 'image/webp'], ['.avif', 'image/avif'],
  ['.png', 'image/png'], ['.svg', 'image/svg+xml'], ['.woff2', 'font/woff2'], ['.ico', 'image/x-icon'],
]);
const server = createServer((req, res) => {
  const url = new URL(req.url, 'http://127.0.0.1');
  const clean = decodeURIComponent(url.pathname.split('?')[0]).replace(/^\/+/, '');
  const file = path.join(ROOT, clean.endsWith('/') || clean === '' ? clean + 'index.html' : clean);
  if (!fs.existsSync(file) || !fs.statSync(file).isFile()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'Content-Type': MIME.get(path.extname(file).toLowerCase()) || 'application/octet-stream' });
  res.end(fs.readFileSync(file));
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const ORIGIN = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

try {
  const context = await browser.newContext({ viewport: { width: 1400, height: 900 }, javaScriptEnabled: false });
  const page = await context.newPage();
  const requestedImages = [];
  page.on('requestfinished', (req) => {
    if (req.resourceType() === 'image') requestedImages.push(req.url());
  });

  await page.goto(`${ORIGIN}/`, { waitUntil: 'load' });
  await page.waitForTimeout(300);

  const coverAvifRequested = requestedImages.some((u) => /portada-las-manecillas-del-recuerdo-\d+\.avif/.test(u));
  const coverWebpRequested = requestedImages.some((u) => /portada-las-manecillas-del-recuerdo-\d+\.webp/.test(u));
  assert(coverAvifRequested, `Chromium (soporta AVIF) debe solicitar el AVIF de la cubierta; solicitadas: ${requestedImages.join(', ')}`);
  assert(!coverWebpRequested, 'Chromium no debe solicitar el WebP si el AVIF está disponible y es soportado');

  // El derivado cargado conserva las proporciones de la cubierta original.
  const natural = await page.locator('.river-cell--lead img').evaluate((img) => ({
    width: img.naturalWidth,
    height: img.naturalHeight,
  }));
  assert(natural.width > 0 && natural.height > 0, 'la cubierta debe cargarse con dimensiones naturales no nulas');
  const aspect = natural.height / natural.width;
  assert(Math.abs(aspect - 1536 / 1024) < 0.05, `el aspect ratio natural debe conservarse (~1.5), obtenido ${aspect.toFixed(2)}`);

  await context.close();

  // MW-0031: verify both editorial instances and the no-JS fallback.
  for (const javascript of [true, false]) {
    const samuelContext = await browser.newContext({
      viewport: { width: 1400, height: 900 },
      javaScriptEnabled: javascript,
    });
    try {
      const samuelPage = await samuelContext.newPage();
      const requested = [];
      samuelPage.on('request', (request) => {
        if (request.resourceType() === 'image' && /samuel_entre_mundos_3d\.(?:avif|webp)(?:\?|$)/.test(request.url())) {
          requested.push(request.url());
        }
      });
      await samuelPage.route('**/*', (route) =>
        route.request().url().startsWith(`${ORIGIN}/`) ? route.continue() : route.abort());
      await samuelPage.goto(`${ORIGIN}/`, { waitUntil: 'domcontentloaded' });
      if (javascript) {
        await samuelPage.locator('html[data-home-editorial-v3="true"]').waitFor();
      }
      const selectors = javascript
        ? [
            '.yale-tile__media picture > img[src="/assets/samuel_entre_mundos_3d.webp"]',
            '.yale-feature-book__media picture > img[src="/assets/samuel_entre_mundos_3d.webp"]',
          ]
        : ['.promo-band > picture > img[src="/assets/samuel_entre_mundos_3d.webp"]'];
      for (const selector of selectors) {
        const image = samuelPage.locator(selector);
        await image.scrollIntoViewIfNeeded();
        await samuelPage.waitForFunction((s) => {
          const img = document.querySelector(s);
          return Boolean(img && img.complete && img.naturalWidth > 0 &&
            img.currentSrc.endsWith('/assets/samuel_entre_mundos_3d.avif'));
        }, selector);
        const attrs = await image.evaluate((img) => ({
          source: img.parentElement?.querySelector(':scope > source[type="image/avif"]')?.getAttribute('srcset'),
          src: img.getAttribute('src'),
          alt: img.getAttribute('alt'),
          width: img.getAttribute('width'),
          height: img.getAttribute('height'),
          loading: img.getAttribute('loading'),
          decoding: img.getAttribute('decoding'),
          currentSrc: img.currentSrc,
        }));
        assert.equal(attrs.source, '/assets/samuel_entre_mundos_3d.avif');
        assert.equal(attrs.src, '/assets/samuel_entre_mundos_3d.webp');
        assert(attrs.alt, 'Samuel debe conservar un alt descriptivo');
        assert.equal(attrs.width, '1530');
        assert.equal(attrs.height, '2400');
        assert.equal(attrs.loading, javascript && selector.includes('yale-feature-book') ? 'eager' : 'lazy');
        assert.equal(attrs.decoding, 'async');
        assert(attrs.currentSrc.endsWith('.avif'));
      }
      assert(requested.some((url) => /samuel_entre_mundos_3d\.avif(?:\?|$)/.test(url)),
        `Samuel debe solicitar AVIF (JS=${javascript}): ${requested.join(', ')}`);
      assert(!requested.some((url) => /samuel_entre_mundos_3d\.webp(?:\?|$)/.test(url)),
        `Samuel no debe solicitar WebP (JS=${javascript}): ${requested.join(', ')}`);
    } finally {
      await samuelContext.close();
    }
  }
  console.log('image-format-ladder-browser: PASS');
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}
