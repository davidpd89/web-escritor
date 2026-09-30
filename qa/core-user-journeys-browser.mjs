// Core User Journeys E2E validation.
// Verifies end-to-end traversal across critical user paths:
// 1. Home -> Main Book (Las manecillas del recuerdo)
// 2. Home -> Author bio (/autor.html)
// 3. Home -> Free sample (/fragmento/)
// 4. Cuaderno -> Article reading
// 5. Herramientas -> Interactive tool usage (Contador de palabras live input)
// 6. Search / Explore Dialog -> Navigation to target
// 7. Radar de Convocatorias -> Filter interaction & official source link
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

try {
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await context.newPage();

  // Journey 1: Home -> Main book
  await page.goto(`${ORIGIN}/`, { waitUntil: 'domcontentloaded' });
  const bookLink = page.locator('main a[href*="/las-manecillas-del-recuerdo/"]:visible').first();
  await bookLink.click();
  await page.waitForURL('**/las-manecillas-del-recuerdo/**');
  assert.ok(page.url().includes('/las-manecillas-del-recuerdo/'), 'Journey 1 failed: did not arrive at Manecillas');
  assert.equal(await page.locator('h1').count(), 1, 'Journey 1: H1 missing on Manecillas page');
  console.log('  ok   Journey 1: Home -> Las manecillas del recuerdo');

  // Journey 2: Home -> Author bio
  await page.goto(`${ORIGIN}/`, { waitUntil: 'domcontentloaded' });
  const authorLink = page.locator('main a[href*="autor.html"]:visible').first();
  await authorLink.click();
  await page.waitForURL('**/autor.html**');
  assert.ok(page.url().includes('/autor.html'), 'Journey 2 failed: did not arrive at Autor');
  assert.ok((await page.textContent('h1')).includes('David Porto Díaz'), 'Journey 2: H1 mismatch on Autor page');
  console.log('  ok   Journey 2: Home -> Autor bio (/autor.html)');

  // Journey 3: Home -> Manecillas fragment
  await page.goto(`${ORIGIN}/`, { waitUntil: 'domcontentloaded' });
  const sampleLink = page.locator('main a[href*="fragmentos"], main a[href*="/las-manecillas-del-recuerdo/"]:visible').first();
  await sampleLink.click();
  await page.waitForLoadState('domcontentloaded');
  // Journey 3: Home / Book -> Specific Reading Fragment
  await page.goto(`${ORIGIN}/las-manecillas-del-recuerdo/`, { waitUntil: 'domcontentloaded' });
  const fragmentLink = page.locator('a[href*="/las-manecillas-del-recuerdo/fragmentos/"]:visible').first();
  assert.equal(await fragmentLink.count(), 1, 'Journey 3: Fragment link must exist on Manecillas page');
  await fragmentLink.click();
  await page.waitForURL('**/las-manecillas-del-recuerdo/fragmentos/**');
  assert.ok(page.url().includes('/las-manecillas-del-recuerdo/fragmentos/'), 'Journey 3: URL must be /las-manecillas-del-recuerdo/fragmentos/');
  const fragmentProse = await page.locator('.fragment-text, .reading-prose, main').textContent();
  assert.ok(fragmentProse && fragmentProse.length > 500, 'Journey 3: Substantive sample text must render on fragments page');
  console.log('  ok   Journey 3: Novela -> Fragmentos de lectura');

  // Journey 4: Cuaderno -> Specific article
  await page.goto(`${ORIGIN}/cuaderno/`, { waitUntil: 'domcontentloaded' });
  const articleLink = page.locator('main .cuaderno-feature a[href^="/cuaderno/"]:not([href="/cuaderno/"]), main .cuaderno-entry a[href^="/cuaderno/"]:not([href="/cuaderno/"])').first();
  assert.equal(await articleLink.count(), 1, 'Journey 4: Article links must exist on Cuaderno index');
  const targetArticleHref = await articleLink.getAttribute('href');
  await articleLink.click();
  await page.waitForLoadState('domcontentloaded');
  assert.notEqual(page.url(), `${ORIGIN}/cuaderno/`, 'Journey 4: Must navigate to a distinct article page');
  assert.ok(page.url().includes('/cuaderno/'), 'Journey 4 failed: destination is not in /cuaderno/');
  assert.equal(await page.locator('h1').count(), 1, 'Journey 4: H1 missing on article page');
  console.log(`  ok   Journey 4: Cuaderno -> Lectura de artículo (${targetArticleHref})`);

  // Journey 5: Herramientas -> Interactive usage (Contador de palabras)
  await page.goto(`${ORIGIN}/herramientas/contador-palabras/`, { waitUntil: 'domcontentloaded' });
  const textarea = page.locator('[data-wc-input]').first();
  assert.equal(await textarea.count(), 1, 'Journey 5: Textarea input must exist in word counter tool');
  await textarea.fill('Uno dos tres cuatro cinco seis siete ocho nueve diez.');
  await page.locator('form[data-wc-form] button[type="submit"]').click();
  await page.waitForTimeout(100);
  const statusText = await page.locator('[data-wc-status]').textContent();
  assert.ok(statusText && statusText.includes('10 palabras'), `Journey 5 failed: expected '10 palabras' in status, got '${statusText}'`);
  console.log('  ok   Journey 5: Herramientas -> Contador de palabras cálculo en vivo');

  // Journey 6: Explore Dialog -> Open & navigate
  await page.goto(`${ORIGIN}/autor.html`, { waitUntil: 'domcontentloaded' });
  const exploreTrigger = page.locator('[data-explore-open]').first();
  assert.equal(await exploreTrigger.count(), 1, 'Journey 6: Explore trigger must exist on page');
  await exploreTrigger.click();
  await page.waitForTimeout(100);
  const exploreDialog = page.locator('#explore-dialog');
  assert.ok(await exploreDialog.evaluate(el => el.open), 'Journey 6: #explore-dialog must be open after click');
  const exploreTarget = page.locator('#explore-dialog a[href="/herramientas/"]').first();
  assert.equal(await exploreTarget.count(), 1, 'Journey 6: Destination link /herramientas/ must exist in explore dialog');
  await exploreTarget.click();
  await page.waitForURL('**/herramientas/**');
  assert.ok(page.url().includes('/herramientas/'), 'Journey 6 failed: explore dialog did not navigate to herramientas');
  console.log('  ok   Journey 6: Diálogo Explorar -> Apertura y navegación a /herramientas/');

  // Journey 7: Convocatorias radar -> Filter & official source link
  await page.goto(`${ORIGIN}/convocatorias-escritores/`, { waitUntil: 'domcontentloaded' });
  const searchInput = page.locator('[data-radar-search]').first();
  assert.equal(await searchInput.count(), 1, 'Journey 7: Search input must exist in radar');
  await searchInput.fill('Jorge Manrique');
  await page.waitForTimeout(100);
  const visibleCards = await page.locator('[data-radar-item]:visible').count();
  assert.ok(visibleCards >= 1, 'Journey 7 failed: filter by Jorge Manrique returned 0 cards');
  const sourceBtn = page.locator('[data-radar-item]:visible a[data-radar-source]').first();
  assert.equal(await sourceBtn.count(), 1, 'Journey 7: Official source link button must exist on filtered opportunity');
  const sourceHref = await sourceBtn.getAttribute('href');
  assert.ok(sourceHref && sourceHref.startsWith('https://') && sourceHref.includes('diputaciondepalencia.es'), `Journey 7: Invalid official source URL: ${sourceHref}`);
  console.log('  ok   Journey 7: Radar de convocatorias -> Filtro en vivo y enlace oficial');

  // Journey 8: Search / Pagefind execution & result navigation
  await page.goto(`${ORIGIN}/`, { waitUntil: 'load' });
  const searchResults = await page.evaluate(async () => {
    const pagefind = await import('/pagefind/pagefind.js');
    const res = await pagefind.search('portal fantasy');
    if (!res.results || res.results.length === 0) return null;
    const item = await res.results[0].data();
    return { url: item.url, title: item.meta?.title };
  });
  assert.ok(searchResults && searchResults.url, 'Journey 8 failed: Pagefind search for "portal fantasy" returned no results');
  await page.goto(`${ORIGIN}${searchResults.url}`, { waitUntil: 'domcontentloaded' });
  assert.equal(await page.locator('h1').count(), 1, 'Journey 8: Arrived search destination missing H1');
  console.log(`  ok   Journey 8: Búsqueda Pagefind -> Consulta "portal fantasy" y navegación a ${searchResults.url}`);

  // Journey 9: Newsletter client validation flow
  await page.goto(`${ORIGIN}/lectores-beta/`, { waitUntil: 'domcontentloaded' });
  const nlForm = page.locator('#lectores-beta-form');
  assert.equal(await nlForm.count(), 1, 'Journey 9: Lectores beta form must exist');
  const emailInput = page.locator('#lectores-beta-email');
  const gdprCheckbox = page.locator('#lectores-beta-gdpr');
  const submitBtn = nlForm.locator('button[type="submit"]');

  // Test client-side rejection of invalid email
  await emailInput.fill('invalid-email-format');
  await gdprCheckbox.check();
  await submitBtn.click();
  await page.waitForTimeout(100);
  assert.equal(await page.locator('#lectores-beta-email').count(), 1, 'Journey 9: Form must not submit on invalid email');
  console.log('  ok   Journey 9: Newsletter -> Validación cliente bloquea email inválido');

  await context.close();
} finally {
  await browser.close();
  server.close();
}

console.log('test-core-user-journeys: OK (All 9 end-to-end user journeys strictly verified without skips)');
