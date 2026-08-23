// AF.5 — proves the materialized /pagefind/ index actually answers queries
// through the exact client API assets/assistant.js already calls
// (`pagefindFallback()`: `import('/pagefind/pagefind.js')` then
// `pagefind.search(query)`), and that publication-gate/searchIndex
// exclusions hold for the real, committed index — not just the Python
// eligibility function in isolation (see tests/test-build-pagefind-index.py
// for that unit-level coverage).
import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const MIME = new Map([
  ['.html', 'text/html; charset=utf-8'], ['.css', 'text/css; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'], ['.json', 'application/json'],
  ['.webp', 'image/webp'], ['.png', 'image/png'], ['.svg', 'image/svg+xml'],
  ['.woff2', 'font/woff2'], ['.ico', 'image/x-icon'],
]);
const server = createServer((req, res) => {
  const url = new URL(req.url, 'http://127.0.0.1');
  const clean = decodeURIComponent(url.pathname.split('?')[0]).replace(/^\/+/, '');
  const file = path.join(ROOT, clean.endsWith('/') || clean === '' ? clean + 'index.html' : clean);
  if (!fs.existsSync(file) || !fs.statSync(file).isFile()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'Content-Type': MIME.get(path.extname(file).toLowerCase()) || 'application/octet-stream' });
  res.end(fs.readFileSync(file));
});
await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const ORIGIN = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({
  headless: true,
  ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}),
});

async function search(page, query) {
  return page.evaluate(async (q) => {
    const pagefind = await import('/pagefind/pagefind.js');
    const result = await pagefind.search(q);
    const items = await Promise.all((result.results || []).map((r) => r.data()));
    return items.map((item) => ({ url: item.url, title: item.meta?.title || '' }));
  }, query);
}

try {
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.goto(`${ORIGIN}/`, { waitUntil: 'load' });

  // pagefind.js itself and its manifest are served with 200 (staging/prod
  // parity for this is covered separately by tests/test-staging-smoke.mjs).
  const pfResponse = await page.request.get(`${ORIGIN}/pagefind/pagefind.js`);
  assert.equal(pfResponse.status(), 200, '/pagefind/pagefind.js must be servable');

  // 1. A real public page answers a real query with a real internal URL.
  const manecillas = await search(page, 'manecillas');
  assert.ok(manecillas.length > 0, 'a simple query must return at least one result');
  assert.ok(
    manecillas.some((item) => /^\/(las-manecillas-del-recuerdo|libros)\//.test(item.url)),
    `expected a Manecillas-related URL among results, got: ${JSON.stringify(manecillas)}`,
  );

  // 2. searchIndex:false content must not surface even via distinctive terms.
  const privacidad = await search(page, 'política de privacidad datos personales');
  assert.ok(
    !privacidad.some((item) => item.url === '/privacidad.html'),
    `/privacidad.html has searchIndex:false and must not appear, got: ${JSON.stringify(privacidad)}`,
  );

  // 3. Gated/staging content (content-registry status != "public") must not surface.
  const jaula = await search(page, 'dónde empieza la jaula');
  assert.ok(
    !jaula.some((item) => item.url.includes('donde-empieza-la-jaula')),
    `gated route must not appear in the local index, got: ${JSON.stringify(jaula)}`,
  );

  // 4. No external network requests during a search (fully local/static).
  const external = [];
  page.on('request', (req) => {
    if (!req.url().startsWith(ORIGIN)) external.push(req.url());
  });
  await search(page, 'herramientas');
  assert.deepEqual(external, [], `local search must not issue external requests, saw: ${JSON.stringify(external)}`);

  await context.close();

  console.log('test-pagefind-search: PASS');
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}
