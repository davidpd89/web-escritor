import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const ROOT = path.resolve(fileURLToPath(new URL('../', import.meta.url)));
const ORIGIN = 'https://david-porto-preview.davidpd89.workers.dev';
const MIME = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.avif': 'image/avif', '.woff2': 'font/woff2', '.ico': 'image/x-icon', '.txt': 'text/plain' };

export async function withJaula(callback, options = {}) {
  const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
  const context = await browser.newContext({ viewport: { width: options.width || 390, height: options.height || 844 }, javaScriptEnabled: options.javaScriptEnabled !== false, reducedMotion: 'reduce', serviceWorkers: 'block' });
  const blocked = [];
  const missing = [];
  const served = [];
  try {
    await context.route('**/*', async route => {
      const request = route.request();
      const url = new URL(request.url());
      if (url.origin !== ORIGIN) {
        blocked.push({ url: url.href, method: request.method() });
        await route.abort();
        return;
      }
      if ((options.failPaths || []).some(value => url.pathname.endsWith(value))) {
        await route.abort();
        return;
      }
      const relative = decodeURIComponent(url.pathname).replace(/^\/+/, '');
      const filename = path.resolve(ROOT, relative.endsWith('/') || !relative ? `${relative}index.html` : relative);
      if (!filename.startsWith(ROOT + path.sep)) {
        await route.fulfill({ status: 403, body: 'Forbidden' });
        return;
      }
      try {
        const body = await fs.readFile(filename);
        served.push({ path: url.pathname, bytes: body.length, type: request.resourceType() });
        await route.fulfill({ status: 200, contentType: MIME[path.extname(filename)] || 'application/octet-stream', body });
      } catch {
        missing.push({ path: url.pathname, type: request.resourceType() });
        await route.fulfill({ status: 404, body: 'Not found' });
      }
    });
    const page = await context.newPage();
    const response = await page.goto(`${ORIGIN}/donde-empieza-la-jaula/`, { waitUntil: 'domcontentloaded', timeout: 20000 });
    assert.ok(response?.ok(), 'La ruta de Jaula no carga en la fixture local');
    await page.evaluate(() => document.fonts?.ready);
    await callback({ page, context, blocked, missing, served });
  } finally {
    await browser.close();
  }
}
