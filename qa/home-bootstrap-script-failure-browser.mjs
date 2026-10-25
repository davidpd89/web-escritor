import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import { readFileSync, existsSync, statSync } from 'node:fs';
import { resolve, sep, extname } from 'node:path';

const ROOT = process.cwd();
const mime = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.mjs': 'text/javascript', '.woff2': 'font/woff2', '.webp': 'image/webp', '.png': 'image/png', '.svg': 'image/svg+xml' };
const server = createServer((req, res) => {
  const name = decodeURIComponent(new URL(req.url, 'http://localhost').pathname).replace(/^\/+/, '');
  const file = resolve(ROOT, name.endsWith('/') || !name ? `${name}index.html` : name);
  if (!file.startsWith(ROOT + sep) || !existsSync(file) || !statSync(file).isFile()) {
    res.writeHead(404); res.end(); return;
  }
  res.writeHead(200, { 'Content-Type': mime[extname(file)] || 'application/octet-stream' });
  res.end(readFileSync(file));
});
await new Promise(resolveListen => server.listen(0, '127.0.0.1', resolveListen));
const origin = `http://127.0.0.1:${server.address().port}`;
let browser;
try {
  browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
  await page.route('**/assets/v1-shell.js*', route => route.abort());
  await page.goto(origin + '/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(6200);
  const state = await page.evaluate(() => {
    const river = document.querySelector('.river-grid');
    const faq = document.querySelector('#faq');
    const link = river?.querySelector('a[href]');
    const visible = el => el && getComputedStyle(el).visibility === 'visible' && getComputedStyle(el).display !== 'none';
    return { river: visible(river), faq: visible(faq), href: link?.getAttribute('href') || '' };
  });
  assert.equal(state.river, true, 'Home remains blank when v1-shell.js is blocked');
  assert.equal(state.faq, true, 'FAQ remains invisible when v1-shell.js fails');
  assert.ok(state.href.startsWith('/') && state.href !== '/null', 'Fallback lacks useful navigation');
} finally {
  await browser?.close();
  await new Promise(resolveClose => server.close(resolveClose));
}
console.log('PASS: Home survives failure of its primary bootstrap script');
