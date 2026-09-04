// AF.5 — proves the materialized /pagefind/ index actually answers queries
// through the exact client API assets/assistant.js already calls
// (`pagefindFallback()`: `import('/pagefind/pagefind.js')` then
// `pagefind.search(query)`), and that publication-gate/searchIndex
// exclusions hold for the real, committed index — not just the Python
// eligibility function in isolation (see tests/test-build-pagefind-index.py
// for that unit-level coverage).
//
// Lives under qa/ (not tests/) because it needs `playwright`: tool-tests.yml
// runs every tests/*.mjs with plain Node and no npm install, so a Playwright
// import there fails with ERR_MODULE_NOT_FOUND. qa/*.mjs browser suites are
// only run by workflows that already do `npm ci` first (here:
// assistant-hardening-qa.yml's browser-qa job).
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
  // parity for this is a follow-up once staging redeploys with this commit;
  // see docs/PENDIENTE-AF-ASSISTANT-PAGEFIND-LOCAL-SEARCH.md).
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

  // 4. Shell-chrome contamination guard (GPT audit item 43, 2026-09-04):
  // header/Explorar/footer are identical on every page and excluded from the
  // index via --exclude-selectors in scripts/build-pagefind-index.py
  // specifically so a term that only appears in that shared chrome (e.g. the
  // header's "Comprar" button, Explorar's "Comprar en Kindle" child link)
  // doesn't return dozens of unrelated pages. This locks that behavior in
  // functionally: if the exclusion selector ever regresses (e.g. a class
  // rename), this is what would catch it, not a visual/manual check.
  for (const q of ['Kindle', 'Comprar en Kindle']) {
    const kindle = await search(page, q);
    assert.ok(kindle.length > 0, `"${q}" must return at least one real result`);
    // A generous ceiling, not an exact count: real pages legitimately mention
    // Kindle now (the landing page itself, the book page, fragmentos,
    // empieza-aqui, prensa's press kit). What this guards against is the
    // header/Explorar/footer contamination bug specifically -- if the
    // exclusion selectors ever regressed, EVERY page on the site would match
    // (56 indexed pages), not a small, legitimate handful.
    assert.ok(kindle.length <= 8, `"${q}" returned ${kindle.length} results -- looks like shell-chrome contamination (header/Explorar/footer text leaking into every page), got: ${JSON.stringify(kindle)}`);
    assert.ok(
      kindle.some((item) => item.url === '/las-manecillas-del-recuerdo/kindle/'),
      `"${q}" must surface the Kindle landing page itself, got: ${JSON.stringify(kindle)}`,
    );
  }

  // 5. No external network requests during a search (fully local/static).
  const external = [];
  page.on('request', (req) => {
    if (!req.url().startsWith(ORIGIN)) external.push(req.url());
  });
  await search(page, 'herramientas');
  assert.deepEqual(external, [], `local search must not issue external requests, saw: ${JSON.stringify(external)}`);

  await context.close();

  console.log('pagefind-search-browser: PASS');
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}
