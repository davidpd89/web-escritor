import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { createServer } from 'node:http';
import { chromium } from 'playwright';

const ROOT = process.cwd();
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml', '.woff2': 'font/woff2' };
const server = createServer((req, res) => {
  const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  const relative = pathname.endsWith('/') ? pathname + 'index.html' : pathname;
  const file = path.resolve(ROOT, '.' + relative);
  if (!file.startsWith(ROOT + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'Content-Type': MIME[path.extname(file)] || 'application/octet-stream' });
  res.end(fs.readFileSync(file));
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  for (const route of ['/las-manecillas-del-recuerdo/', '/las-manecillas-del-recuerdo/fragmentos/', '/libros/samuel-entre-mundos/', '/cuaderno/', '/herramientas/distribucion-pov/']) {
    const context = await browser.newContext();
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.route('**/*', request => new URL(request.request().url()).origin === origin ? request.continue() : request.abort());
    const response = await page.goto(origin + route, { waitUntil: 'load' });
    assert.equal(response?.status(), 200, route);
    assert.ok(await page.locator('main').count(), `${route}: falta main`);
    assert.ok(await page.locator('h1').count(), `${route}: falta H1`);
    assert.ok((await page.locator('main').innerText()).trim().length > 100, `${route}: contenido vacío`);
    assert.deepEqual(errors, [], `${route}: ${errors.join(' | ')}`);
    await context.close();
  }
  console.log('CI THIRD PARTY OUTAGE: OK');
} finally {
  await browser.close();
  await new Promise(resolve => server.close(resolve));
}