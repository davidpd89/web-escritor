import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
export const ORIGIN = 'https://qa-home.invalid';

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.json': 'application/json',
  '.webp': 'image/webp',
  '.avif': 'image/avif',
  '.jpg': 'image/jpeg',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.woff2': 'font/woff2'
};

export async function localPage(browser, options = {}) {
  const context = await browser.newContext({
    viewport: { width: 1280, height: 900 },
    reducedMotion: 'reduce',
    ...options
  });

  await context.route('**/*', async route => {
    const url = new URL(route.request().url());
    if (url.origin !== ORIGIN) {
      await route.abort();
      return;
    }

    let name;
    try {
      name = decodeURIComponent(url.pathname).replace(/^\/+/, '');
    } catch {
      await route.fulfill({ status: 400, body: 'Invalid URL' });
      return;
    }
    if (!name || name.endsWith('/')) name += 'index.html';
    const file = path.resolve(ROOT, name);
    if (!file.startsWith(ROOT + path.sep)) {
      await route.fulfill({ status: 403, body: 'Forbidden' });
      return;
    }
    if (!fs.existsSync(file) || !fs.statSync(file).isFile()) {
      await route.fulfill({
        status: 404,
        contentType: MIME['.html'],
        body: fs.readFileSync(path.join(ROOT, '404.html'))
      });
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: MIME[path.extname(file).toLowerCase()] || 'application/octet-stream',
      body: fs.readFileSync(file)
    });
  });

  return { context, page: await context.newPage(), origin: ORIGIN };
}

export async function readyHome(page) {
  await page.addInitScript(() => {
    sessionStorage.setItem('dp-intro-seen', '1');
  });
  await page.goto(ORIGIN + '/', { waitUntil: 'load' });
  await page.locator('[data-editorial-home-flow]').waitFor({ timeout: 12000 });
}