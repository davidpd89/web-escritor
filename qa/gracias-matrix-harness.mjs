import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { createServer } from 'node:http';
import { chromium } from 'playwright';

const ROOT = process.cwd();
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml', '.webp': 'image/webp', '.jpg': 'image/jpeg', '.png': 'image/png', '.woff2': 'font/woff2', '.ico': 'image/x-icon' };

export async function withSite(fn) {
  const server = createServer((req, res) => {
    try {
      const relative = decodeURIComponent(new URL(req.url, 'http://localhost').pathname).replace(/^\/+/, '');
      const filename = path.resolve(ROOT, relative.endsWith('/') || !relative ? relative + 'index.html' : relative);
      if (!filename.startsWith(ROOT + path.sep)) return res.writeHead(403).end();
      const data = fs.readFileSync(filename);
      res.writeHead(200, { 'content-type': TYPES[path.extname(filename)] || 'application/octet-stream' }).end(data);
    } catch { res.writeHead(404).end(); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  let browser;
  try {
    browser = await chromium.launch({ headless: true });
    const open = async (route = '/gracias-suscripcion/', options = {}, setup = null) => {
      const context = await browser.newContext({ viewport: { width: 390, height: 844 }, ...options });
      await context.route('**/*', r => new URL(r.request().url()).origin === base ? r.continue() : r.fulfill({ status: 204, body: '' }));
      const page = await context.newPage();
      if (setup) await setup({ page, context, base });
      const response = await page.goto(base + route, { waitUntil: 'domcontentloaded' });
      assert.equal(response?.status(), 200, `${route}: local HTTP status`);
      return { page, context };
    };
    await fn({ base, browser, open });
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
}
