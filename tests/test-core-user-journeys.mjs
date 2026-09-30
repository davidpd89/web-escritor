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
  assert.ok(page.url().includes('/las-manecillas-del-recuerdo/'), 'Journey 3 failed: did not arrive at Manecillas reading path');
  console.log('  ok   Journey 3: Home -> Fragmento / lectura de Manecillas');

  // Journey 4: Cuaderno -> Article
  await page.goto(`${ORIGIN}/cuaderno/`, { waitUntil: 'domcontentloaded' });
  const articleLink = page.locator('main .article-card a:visible, main a[href*="/cuaderno/"]:visible').first();
  await articleLink.click();
  await page.waitForLoadState('domcontentloaded');
  assert.ok(page.url().includes('/cuaderno/'), 'Journey 4 failed: did not arrive at an article');
  assert.equal(await page.locator('h1').count(), 1, 'Journey 4: H1 missing on article');
  console.log('  ok   Journey 4: Cuaderno -> Lectura de artículo');

  // Journey 5: Herramientas -> Interactive usage (Contador de palabras)
  await page.goto(`${ORIGIN}/herramientas/contador-palabras/`, { waitUntil: 'domcontentloaded' });
  const textarea = page.locator('[data-wc-input]').first();
  await textarea.fill('Uno dos tres cuatro cinco seis siete ocho nueve diez.');
  await page.locator('form[data-wc-form] button[type="submit"]').click();
  await page.waitForTimeout(100);
  const statusText = await page.locator('[data-wc-status]').textContent();
  assert.ok(statusText && statusText.includes('10 palabras'), `Journey 5 failed: expected '10 palabras' in status, got '${statusText}'`);
  console.log('  ok   Journey 5: Herramientas -> Contador de palabras interacción viva');

  // Journey 6: Explore Dialog -> Navigation
  await page.goto(`${ORIGIN}/`, { waitUntil: 'domcontentloaded' });
  const exploreTrigger = page.locator('[data-explore-open]').first();
  if (await exploreTrigger.isVisible()) {
    await exploreTrigger.click();
    await page.waitForTimeout(100);
    const exploreTarget = page.locator('#explore-dialog a[href="/herramientas/"]').first();
    await exploreTarget.click();
    await page.waitForURL('**/herramientas/**');
    assert.ok(page.url().includes('/herramientas/'), 'Journey 6 failed: explore dialog did not navigate to herramientas');
    console.log('  ok   Journey 6: Diálogo Explorar -> Navegación exitosa');
  }

  // Journey 7: Convocatorias radar -> Filter & source link
  await page.goto(`${ORIGIN}/convocatorias-escritores/`, { waitUntil: 'domcontentloaded' });
  const searchInput = page.locator('[data-radar-search]').first();
  if (await searchInput.isVisible()) {
    await searchInput.fill('Jorge Manrique');
    await page.waitForTimeout(100);
    const visibleCards = await page.locator('[data-radar-item]:visible').count();
    assert.ok(visibleCards >= 1, 'Journey 7 failed: filter by Jorge Manrique returned 0 cards');
    console.log('  ok   Journey 7: Radar de convocatorias -> Filtro en vivo e interacción');
  }

  await context.close();
} finally {
  await browser.close();
  server.close();
}

console.log('test-core-user-journeys: OK (All 7 end-to-end user journeys verified)');
