import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { createServer } from 'node:http';
import { chromium } from 'playwright';

const ROOT = process.cwd();
const TYPES = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json', '.svg': 'image/svg+xml', '.woff2': 'font/woff2' };
const server = createServer((req, res) => {
  const url = new URL(req.url, 'http://localhost');
  const relative = url.pathname.endsWith('/') ? url.pathname + 'index.html' : url.pathname;
  const file = path.resolve(ROOT, '.' + decodeURIComponent(relative));
  if (!file.startsWith(ROOT + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream' });
  res.end(fs.readFileSync(file));
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  for (const route of ['/libros/', '/cuaderno/', '/herramientas/distribucion-pov/', '/ferias.html']) {
    const page = await browser.newPage({ viewport: { width: 320, height: 740 }, reducedMotion: 'reduce' });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.route('**/*', request => new URL(request.request().url()).origin === origin ? request.continue() : request.abort());
    const response = await page.goto(origin + route, { waitUntil: 'load' });
    assert.equal(response?.status(), 200, route);
    await page.addStyleTag({ url: origin + '/qa/text-spacing.css' });
    await page.evaluate(() => document.fonts?.ready);
    const metrics = await page.evaluate(() => ({ scroll: document.documentElement.scrollWidth, viewport: document.documentElement.clientWidth }));
    assert.ok(metrics.scroll <= metrics.viewport + 1, `${route}: overflow ${metrics.scroll}/${metrics.viewport}`);
    const action = page.locator('main a[href]:visible, main button:visible').first();
    assert.ok(await action.count(), `${route}: no hay controles visibles`);
    await action.focus();
    assert.ok(await action.evaluate(element => element === document.activeElement), `${route}: control no enfocable`);
    assert.deepEqual(errors, [], `${route}: ${errors.join(' | ')}`);
    await page.close();
  }
  console.log('CI CROSS FAMILY TEXT SPACING: OK');
} finally {
  await browser.close();
  await new Promise(resolve => server.close(resolve));
}