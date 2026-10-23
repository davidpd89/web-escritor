import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { createServer } from 'node:http';
import { chromium } from 'playwright';

const ROOT = process.cwd();
const server = createServer((req, res) => {
  const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  const file = path.resolve(ROOT, '.' + (pathname.endsWith('/') ? pathname + 'index.html' : pathname));
  if (!file.startsWith(ROOT + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) { res.writeHead(404); res.end(); return; }
  const ext = path.extname(file);
  res.setHeader('Content-Type', { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml' }[ext] || 'application/octet-stream');
  res.end(fs.readFileSync(file));
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  for (const id of ['fragmento-1', 'fragmento-2', 'fragmento-3']) {
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.route('**/*', async route => {
      if (new URL(route.request().url()).origin !== origin) return route.abort();
      if (route.request().url().includes('/assets/v1-fragments.js')) await new Promise(resolve => setTimeout(resolve, 450));
      return route.continue();
    });
    const response = await page.goto(`${origin}/las-manecillas-del-recuerdo/fragmentos/#${id}`, { waitUntil: 'load' });
    assert.equal(response?.status(), 200);
    await page.waitForFunction(id => document.querySelector(`[data-fragment-link="${id}"]`)?.getAttribute('data-current') === 'true', id, { timeout: 5000 });
    assert.equal(new URL(page.url()).hash, `#${id}`);
    assert.equal(await page.locator('.excerpt-section').count(), 3);
    assert.deepEqual(errors, [], `${id}: ${errors.join(' | ')}`);
    await page.close();
  }
  console.log('CI DELAYED FRAGMENTS: OK');
} finally {
  await browser.close();
  await new Promise(resolve => server.close(resolve));
}