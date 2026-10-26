import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const MIME = new Map([
  ['.html', 'text/html; charset=utf-8'],
  ['.css', 'text/css; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'],
  ['.svg', 'image/svg+xml'],
  ['.woff2', 'font/woff2']
]);

const server = createServer((req, res) => {
  const pathname = new URL(req.url, 'http://127.0.0.1').pathname;
  const relative = decodeURIComponent(pathname).replace(/^\/+/, '');
  const file = path.resolve(ROOT, relative.endsWith('/') ? relative + 'index.html' : relative);
  if (!file.startsWith(ROOT + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) {
    res.writeHead(404);
    res.end();
    return;
  }
  res.writeHead(200, {
    'Content-Type': MIME.get(path.extname(file)) || 'application/octet-stream'
  });
  res.end(fs.readFileSync(file));
});

await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ headless: true });

try {
  const context = await browser.newContext();
  await context.route(/^https?:\/\/(?!127\.0\.0\.1)/, route => route.abort());
  const page = await context.newPage();

  for (const route of ['/lectores-beta/', '/lectores-beta/enviar-manuscrito/']) {
    const response = await page.goto(origin + route, { waitUntil: 'domcontentloaded' });
    assert.equal(response?.status(), 200, `${route}: HTTP 200`);

    const state = await page.locator('nav.section-context').evaluate(nav => {
      const current = [...nav.querySelectorAll('a[aria-current="page"]')];
      return current.map(link => ({
        text: link.textContent.trim(),
        path: new URL(link.href).pathname
      }));
    });

    if (route === '/lectores-beta/') {
      assert.deepEqual(state, [
        { text: 'Lectores beta', path: '/lectores-beta/' }
      ], 'La página de alta debe identificarse como actual');
    } else {
      assert.ok(
        state.every(item => item.path === route),
        `${route}: aria-current apunta a otra página: ${JSON.stringify(state)}`
      );
    }
  }

  await page.goto(origin + '/lectores-beta/');
  const destination = page.locator('main a[href="/lectores-beta/enviar-manuscrito/"]');
  assert.equal(await destination.count(), 1, 'Debe existir el enlace de envío de manuscritos');
  await destination.click();
  await page.waitForURL('**/lectores-beta/enviar-manuscrito/');

  const incorrectCurrent = await page.locator(
    'nav.section-context a[href="/lectores-beta/"][aria-current="page"]'
  ).count();
  assert.equal(
    incorrectCurrent, 0,
    'Tras navegar al envío, Lectores beta no debe anunciarse como página actual'
  );

  console.log('lectores-beta-current-page-parity: PASS');
  await context.close();
} finally {
  await browser.close();
  await new Promise(resolve => server.close(resolve));
}
