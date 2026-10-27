import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const MIME = new Map([['.html', 'text/html; charset=utf-8'], ['.css', 'text/css; charset=utf-8'], ['.js', 'text/javascript; charset=utf-8'], ['.json', 'application/json; charset=utf-8'], ['.woff2', 'font/woff2']]);
const server = createServer((req, res) => {
  const pathname = new URL(req.url, 'http://127.0.0.1').pathname;
  const relative = pathname.endsWith('/') ? pathname.slice(1) + 'index.html' : pathname.slice(1);
  const file = path.resolve(ROOT, relative);
  if (!file.startsWith(ROOT + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) {
    res.writeHead(404); res.end(); return;
  }
  res.writeHead(200, { 'Content-Type': MIME.get(path.extname(file)) || 'application/octet-stream' });
  res.end(fs.readFileSync(file));
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = process.env.QA_ORIGIN || `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const pages = await Promise.all(Array.from({ length: 6 }, () => context.newPage()));
  await Promise.all(pages.map(async (page, index) => {
    for (let attempt = 0; attempt < 3; attempt++) {
      const response = await page.goto(`${origin}/redes-sociales/`, { waitUntil: 'domcontentloaded' });
      assert.equal(response?.status(), 200, `/redes-sociales/, página ${index}, intento ${attempt}: HTTP incorrecto`);
      const heading = page.locator('h1');
      assert.equal(await heading.count(), 1, `/redes-sociales/, página ${index}: falta H1`);
      assert.ok((await heading.innerText()).trim(), `/redes-sociales/, página ${index}: H1 vacío`);
      const nav = page.locator('header noscript nav.primary-nav');
      assert.equal(await nav.count(), 1, `/redes-sociales/, página ${index}: falta navegación alternativa sin JS`);
      const works = nav.locator('a[href="/libros/"]');
      assert.equal(await works.count(), 1, `/redes-sociales/, página ${index}: falta enlace a obras`);
      assert.ok(await works.isVisible(), `/redes-sociales/, página ${index}: enlace a obras oculto`);
      assert.ok((await page.locator('body').innerText()).trim().length > 100, `/redes-sociales/, página ${index}: cuerpo sin contenido útil`);
    }
  }));
  await context.close();
} finally {
  await browser.close();
  await new Promise(resolve => server.close(resolve));
}
console.log('social-nojs-repeated-navigation: OK');
