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
  ['.js', 'text/javascript; charset=utf-8'], ['.webp', 'image/webp'], ['.avif', 'image/avif'],
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
  const context = await browser.newContext({ viewport: { width: 1400, height: 900 } });
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

  // Las dimensiones renderizadas del <img> de la cubierta no deben cambiar.
  const box = await page.locator('.hero-cover img').boundingBox();
  assert(box && box.width > 0 && box.height > 0, 'la cubierta debe renderizarse con dimensiones no nulas');
  const aspect = box.height / box.width;
  assert(Math.abs(aspect - 1536 / 1024) < 0.05, `el aspect ratio debe conservarse (~1.5), obtenido ${aspect.toFixed(2)}`);

  await context.close();
  console.log('image-format-ladder-browser: PASS');
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}
