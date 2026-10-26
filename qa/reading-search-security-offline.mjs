import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const ROOT = process.cwd();
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json' };
const server = createServer((req, res) => {
  const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  const filename = path.resolve(ROOT, '.' + pathname, pathname.endsWith('/') ? 'index.html' : '');
  if (!filename.startsWith(ROOT + path.sep) || !fs.existsSync(filename) || !fs.statSync(filename).isFile()) {
    res.writeHead(404); res.end('Not found'); return;
  }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(filename)] || 'application/octet-stream' });
  res.end(fs.readFileSync(filename));
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = 'http://127.0.0.1:' + server.address().port;
const browser = await chromium.launch({ headless: true });
const attacks = [
  '<svg data-qa-xss onload="window.__qaInjected=1">',
  '<img data-qa-xss src=x onerror="window.__qaInjected=1">',
  '%E0%A4%A',
  'javascript:alert(1)',
  'ñ á ü 日本語',
  'x'.repeat(200),
];
try {
  const context = await browser.newContext({ serviceWorkers: 'block' });
  await context.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
  const page = await context.newPage();
  const initialResponse = await page.goto(origin + '/recomendaciones/', { waitUntil: 'domcontentloaded' });
  assert.equal(initialResponse?.status(), 200, 'El catálogo debe responder HTTP 200');
  for (const value of attacks) {
    await page.goto(origin + '/recomendaciones/#q=' + encodeURIComponent(value), { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(v => document.querySelector('input[data-filter="q"]')?.value === v, value);
    const result = await page.evaluate(() => ({
      injected: Boolean(window.__qaInjected),
      nodes: document.querySelectorAll('[data-qa-xss]').length,
      cards: document.querySelectorAll('[data-catalogue-book]').length,
    }));
    assert.equal(result.injected, false, value);
    assert.equal(result.nodes, 0, value);
    assert.ok(result.cards > 0, 'El catálogo perdió sus fichas');
  }
  await context.close();
} finally {
  await browser.close();
  await new Promise(resolve => server.close(resolve));
}
console.log('PASS buscador seguro offline: ' + attacks.length + ' entradas');
