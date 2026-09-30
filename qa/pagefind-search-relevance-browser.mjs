// Human search relevance & quality benchmark for Pagefind search index.
// Validates query accuracy, ranking of canonical destinations, accent tolerance,
// zero-results cleanliness, and strict exclusion of noindex pages.
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const ROOT = process.cwd();
const MIME = new Map([
  ['.html', 'text/html; charset=utf-8'], ['.css', 'text/css; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'], ['.mjs', 'text/javascript; charset=utf-8'],
  ['.json', 'application/json'], ['.wasm', 'application/wasm'],
  ['.webp', 'image/webp'], ['.png', 'image/png'], ['.svg', 'image/svg+xml'],
  ['.woff2', 'font/woff2'], ['.ico', 'image/x-icon'], ['.pf_meta', 'application/octet-stream'],
  ['.pagefind', 'text/javascript; charset=utf-8'],
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

async function runSearch(page, query) {
  return page.evaluate(async (q) => {
    const pagefind = await import('/pagefind/pagefind.js');
    const result = await pagefind.search(q);
    const items = await Promise.all((result.results || []).slice(0, 5).map(async (r) => {
      const data = await r.data();
      return { url: data.url, title: data.meta?.title || '', score: r.score };
    }));
    return items;
  }, query);
}

const page = await browser.newPage();
await page.goto(`${ORIGIN}/`, { waitUntil: 'load' });

const BENCHMARK = [
  { query: 'David Porto', expectedPattern: /autor\.html/ },
  { query: 'Las manecillas del recuerdo', expectedPattern: /\/las-manecillas-del-recuerdo\// },
  { query: 'Samuel entre mundos', expectedPattern: /\/(libros\/samuel-entre-mundos|fragmento)\// },
  { query: 'portal fantasy', expectedPattern: /\/(que-es-el-portal-fantasy|portal-fantasy-espanol|portal-fantasy-vs-fantasia-epica)\// },
  { query: 'sistema de magia', expectedPattern: /\/(sistema-de-magia-noveris|magia-con-coste|libros\/samuel-entre-mundos)\// },
  { query: 'editoriales', expectedPattern: /\/editoriales\// },
  { query: 'convocatorias', expectedPattern: /\/convocatorias-escritores\// },
  { query: 'contador de palabras', expectedPattern: /\/herramientas\/contador-palabras\// },
  { query: 'legibilidad', expectedPattern: /\/herramientas\/legibilidad\// },
  { query: 'fantasia', expectedPattern: /\/(cuaderno|recomendaciones)\// },
  { query: 'poesía', expectedPattern: /\/convocatorias-escritores\// },
];

for (const { query, expectedPattern } of BENCHMARK) {
  const results = await runSearch(page, query);
  const match = results.some(r => expectedPattern.test(r.url));
  assert.ok(match, `Query "${query}" failed to surface expected destination matching ${expectedPattern}. Results: ${JSON.stringify(results)}`);
}

// Zero results check: distinct non-matching query returns 0 results
const emptyResults = await runSearch(page, 'zzqqwwjjkk99inexistente');
assert.equal(emptyResults.length, 0, 'Inexistent query must return 0 results');

// Noindex check: private/staging pages never leak in public search
const noindexResults = await runSearch(page, 'aviso legal responsabilidad');
const leaksNoindex = noindexResults.some(r => r.url === '/aviso-legal.html' || r.url === '/privacidad.html');
assert.equal(leaksNoindex, false, 'Noindex pages must not appear in search results');

await browser.close();
server.close();

console.log('test-pagefind-search-relevance-benchmark: PASS (11 human query patterns, zero-results and noindex exclusion)');
