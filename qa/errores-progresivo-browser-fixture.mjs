import { createServer } from 'node:http';
import { readFileSync, existsSync, statSync } from 'node:fs';
import { resolve, relative, extname, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const ROOT = resolve(fileURLToPath(new URL('..', import.meta.url)));
const MIME = new Map([
  ['.html', 'text/html; charset=utf-8'], ['.js', 'text/javascript; charset=utf-8'],
  ['.mjs', 'text/javascript; charset=utf-8'], ['.css', 'text/css; charset=utf-8'],
  ['.json', 'application/json; charset=utf-8'], ['.png', 'image/png'],
  ['.svg', 'image/svg+xml'], ['.webp', 'image/webp'], ['.woff2', 'font/woff2'],
]);
export async function startSite(overrides = {}) {
  const server = createServer((request, response) => {
    let pathname;
    try { pathname = decodeURIComponent(new URL(request.url, 'http://127.0.0.1').pathname); }
    catch { response.writeHead(400).end(); return; }
    if (Object.hasOwn(overrides, pathname)) {
      response.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      response.end(overrides[pathname]);
      return;
    }
    const rel = pathname.endsWith('/') ? pathname + 'index.html' : pathname;
    const file = resolve(ROOT, '.' + rel);
    const inside = !relative(ROOT, file).startsWith('..' + sep) && relative(ROOT, file) !== '..';
    if (!inside || !existsSync(file) || !statSync(file).isFile()) {
      response.writeHead(404, { 'Content-Type': 'text/html; charset=utf-8' });
      response.end(readFileSync(resolve(ROOT, '404.html')));
      return;
    }
    response.writeHead(200, { 'Content-Type': MIME.get(extname(file)) || 'application/octet-stream' });
    response.end(readFileSync(file));
  });
  await new Promise(done => server.listen(0, '127.0.0.1', done));
  return {
    origin: `http://127.0.0.1:${server.address().port}`,
    close: () => new Promise(done => server.close(done)),
  };
}
export const launch = () => chromium.launch({
  headless: true,
  ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}),
});
