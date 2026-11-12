import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { auditTargetSizes } from './target-size-audit.mjs';

const base = process.env.RECOMMENDATIONS_BASE_URL || 'http://127.0.0.1:4173';
const fixturePath = process.env.READING_COMMERCE_FIXTURE_PATH || '.ci/reading-commerce/fixture.json';
await fs.mkdir(path.dirname(fixturePath), { recursive: true });
execFileSync(process.env.PYTHON || 'python', ['tests/test-reading-catalogue.py', '--browser-fixture', fixturePath]);
const fixture = JSON.parse(await fs.readFile(fixturePath, 'utf8'));
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {}) });
const now = new Date('2026-10-20T16:00:00Z');
const dated = { actualizado_en: '2026-10-20T15:00:00Z', caduca_en: '2026-10-21T15:00:00Z' };
const offer = (id, formato, price, extra = {}) => ({ ...dated, libro_id: id, formato, precio_centimos: price, moneda: 'EUR', tipo: 'compra', url: 'https://www.amazon.es/dp/B000000001?tag=contrato-21', ...extra });
const payload = { schema_version: 1, offers: [offer('contrato-uno', 'ebook', 500, { precio_referencia_centimos: 1000 }), offer('contrato-uno', 'tapa-dura', 3000), offer('contrato-dos', 'tapa-blanda', 1500)], ratings: [{ ...dated, libro_id: 'contrato-uno', puntuacion: 4.2, numero_valoraciones: 100, url: 'https://www.goodreads.com/book/show/123' }] };
try {
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.clock.install({ time: now });
  await context.route('**/recomendaciones/?*', route => route.fulfill({ contentType: 'text/html', body: fixture.hub }));
  let market = payload;
  await context.route('**/assets/reading-market.json', route => route.fulfill({ json: market }));
  const errors = []; page.on('pageerror', e => errors.push(e.message));
  const field = name => page.locator(`[data-filter="${name}"]`);
  const ids = () => page.locator('[data-catalogue-book]:not([hidden])').evaluateAll(nodes => nodes.map(n => n.dataset.bookId));
  const open = async () => { await page.goto(`${base}/recomendaciones/?utm_source=prueba`); await field('descuento').waitFor({ state: 'attached' }); await page.waitForFunction(() => !document.querySelector('[data-filter="descuento"]').disabled); await page.locator('details[data-facet-group="formato"]').evaluate(d => { d.open = true; }); };
  await open();
  await page.locator('input[data-facet="formato"][value="tapa-dura"]').check();
  assert.deepEqual(await ids(), ['contrato-uno'], 'Solo contrato-uno tiene una oferta en tapa dura');
  await page.locator('input[data-facet="formato"][value="tapa-dura"]').uncheck(); await page.locator('input[data-facet="formato"][value="ebook"]').check(); assert.deepEqual(await ids(), ['contrato-uno']);
  await field('descuento').selectOption('50'); assert.deepEqual(await ids(), ['contrato-uno']);
  // Umbral que ningún libro cumple: desactivado (antes «50 %» salía activo con cero libros).
  market = { ...payload, offers: [offer('contrato-uno', 'ebook', 800, { precio_referencia_centimos: 1000 })] };
  await page.goto(`${base}/recomendaciones/?utm_source=prueba`); await page.waitForFunction(() => !document.querySelector('[data-filter="descuento"]').disabled);
  assert.deepEqual(await field('descuento').locator('option:disabled').evaluateAll(o => o.map(x => x.value)), ['25', '50']);
  market = payload; await open();
  await page.getByRole('button', { name: 'Restablecer' }).click();
  await page.waitForFunction(() => document.querySelector('[data-catalogue-count]').textContent === '2 libros');
  assert.equal(new URL(page.url()).searchParams.get('utm_source'), 'prueba');
  await field('orden').selectOption('fecha_asc'); assert.deepEqual(await ids(), ['contrato-dos', 'contrato-uno']);
  await field('orden').selectOption('editorial'); assert.deepEqual(await ids(), ['contrato-uno', 'contrato-dos']);
  assert.equal(await field('orden').locator('option[value="titulo"], option[value="titulo_desc"], option[value="autor"]').count(), 0, 'Sin ordenaciones por título o autor');
  // La Creators API no da valoraciones: ni filtro ni orden por nota (David, 08/11).
  assert.equal(await page.locator('[data-filter="valoracion"], option[value="valoracion_desc"]').count(), 0);
  await field('hasta').fill('1990-12-31'); assert.deepEqual(await ids(), ['contrato-dos']);
  await field('hasta').fill('');
  await page.clock.fastForward(25 * 3600000);
  await page.evaluate(() => window.dispatchEvent(new Event('pageshow')));
  assert(await field('descuento').isDisabled());
  assert.equal(await page.locator('[data-price-book]:not([hidden])').count(), 0);
  market = { schema_version: 1, offers: [offer('contrato-uno', 'ebook', 1, { moneda: 'USD' }), offer('contrato-dos', 'ebook', 1, { url: 'https://amazon.es.evil.invalid/dp/B000000001?tag=contrato-21' }), offer('contrato-uno', 'ebook', 1, { actualizado_en: '2027-01-01T00:00:00Z', caduca_en: '2027-01-02T00:00:00Z' })], ratings: [{ ...payload.ratings[0], puntuacion: 6 }] };
  await page.goto(`${base}/recomendaciones/?utm_source=prueba`); await page.waitForLoadState('networkidle');
  assert(await field('descuento').isDisabled());
  assert.equal(await page.locator('[data-price-book]:not([hidden])').count(), 0);
  assert.equal(await page.locator('[data-rating-book]').count(), 0, 'Las tarjetas no llevan valoración');
  assert.equal(await page.locator('.catalogue-stars').count(), 0, 'Ninguna estrella');
  assert.deepEqual(errors, []);
  await context.close();
  // Aunque el mercado traiga notas (Google Books, Hardcover…), fuera de la ficha no se pinta ninguna (David, 08/11).
  const sourceContext = await browser.newContext();
  const sourcePage = await sourceContext.newPage();
  await sourcePage.clock.install({ time: now });
  await sourceContext.route('**/recomendaciones/?*', route => route.fulfill({ contentType: 'text/html', body: fixture.hub }));
  await sourceContext.route('**/assets/reading-market.json', route => route.fulfill({ json: {
    schema_version: 1, offers: [], ratings: [
      { ...dated, libro_id: 'contrato-uno', puntuacion: 4.3, numero_valoraciones: 78, fuente: 'google_books', url: 'https://books.google.com/books?id=ABCD_123' },
      { ...dated, libro_id: 'contrato-dos', puntuacion: 3.9, numero_valoraciones: 201, fuente: 'hardcover', url: 'https://hardcover.app/books/contrato-dos' },
    ] } }));
  await sourcePage.goto(`${base}/recomendaciones/?utm_source=fuentes`, { waitUntil: 'networkidle' });
  assert.equal(await sourcePage.locator('[data-rating-book], .catalogue-stars').count(), 0);
  assert(!/Google Books|Hardcover|★/.test(await sourcePage.locator('main').innerText()), 'Sin notas en el listado');
  await sourceContext.close();
  const monthContext = await browser.newContext();
  const monthPage = await monthContext.newPage();
  await monthPage.route('**/recomendaciones/', route => route.fulfill({ contentType: 'text/html', body: fixture.hub.replace('data-published="1990-01-01"', 'data-published-month="1990-06"') }));
  await monthPage.route('**/assets/reading-market.json', route => route.fulfill({ json: { schema_version: 1, offers: [], ratings: [] } }));
  await monthPage.goto(`${base}/recomendaciones/`);
  await monthPage.locator('[data-filter="desde"]').fill('1990-07-01');
  assert.equal(await monthPage.locator('[data-book-id="contrato-dos"]').isVisible(), false, 'June edition must not match a July lower bound');
  await monthPage.locator('[data-filter="desde"]').fill('');
  await monthPage.locator('[data-filter="hasta"]').fill('1990-05-31');
  assert.equal(await monthPage.locator('[data-catalogue-book]:visible').count(), 0);
  await monthPage.locator('[data-filter="hasta"]').fill('1990-06-15');
  assert.equal(await monthPage.locator('[data-book-id="contrato-dos"]').isVisible(), true, 'Unknown day remains a month interval');
  await monthContext.close();
  const live = await browser.newPage({ viewport: { width: 390, height: 900 } });
  await live.route('**/assets/reading-market.json', route => route.fulfill({ json: { schema_version: 1, offers: [], ratings: [{ ...payload.ratings[0], libro_id: 'lib-0001', actualizado_en: new Date(Date.now() - 3600000).toISOString(), caduca_en: new Date(Date.now() + 3600000).toISOString() }] } }));
  await live.goto(`${base}/`);
  assert.deepEqual(await live.locator('#masthead-submenu-recommendations-hub a').allTextContents(), ['Catálogo de libros', 'Autores', 'Editoriales', 'Atlas literario', 'Concursos']);
  await live.goto(`${base}/recomendaciones/libros/coraline/`);
  // La ficha solo enlaza a Goodreads por ISBN, aunque el mercado traiga una nota (David, 08/11).
  const ratingLink = live.locator('[data-rating-book] a');
  await ratingLink.waitFor();
  assert.match(await ratingLink.getAttribute('href'), /^https:\/\/www\.goodreads\.com\/book\/isbn\/\d{13}$/);
  assert.equal(await ratingLink.innerText(), 'Goodreads · ver opiniones');
  assert.equal(await live.locator('.catalogue-stars').count(), 0);
  const target = await ratingLink.boundingBox();
  assert(target.width >= 44 && target.height >= 44, 'Goodreads must be a usable touch target');
  const formats = await live.locator('[data-purchase-format]').evaluateAll(links => links.map(a => ({ format: a.dataset.purchaseFormat, href: a.href, rel: a.rel })));
  assert.equal(formats.length, 4);
  assert.equal(new Set(formats.map(f => new URL(f.href).pathname)).size, 4);
  for (const f of formats) { assert.equal(new URL(f.href).searchParams.get('tag'), 'davidporto-21'); assert.match(f.rel, /sponsored/); }
  assert.equal(await live.locator('footer a[href="/recomendaciones/politica-de-recomendaciones/"]').count(), 1);
  const author = live.locator('main a[href="/recomendaciones/autores/neil-gaiman/"]').first();
  assert.equal(await author.getAttribute('target'), '_blank');
  await live.goto(`${base}/recomendaciones/autores/neil-gaiman/`);
  assert.equal(await live.locator('main h1').innerText(), 'Neil Gaiman');
  assert.equal(await live.locator('.catalogue-author-books > li').count(), 1);
  // Sin el bloque «Fuentes y ediciones», Wikipedia queda como identidad del autor en sameAs (JSON-LD).
  assert.match(await live.locator('script[type="application/ld+json"]').allInnerTexts().then(t => t.join(' ')), /"sameAs": \[[^\]]*es\.wikipedia\.org\/wiki\/Neil_Gaiman/);
  assert(!/aggregateRating/.test(await live.content()));
  for (const width of [390, 768, 1280]) {
    await live.setViewportSize({ width, height: 900 });
    for (const route of ['/recomendaciones/', '/recomendaciones/libros/coraline/', '/recomendaciones/autores/neil-gaiman/']) {
      await live.goto(base + route, { waitUntil: 'networkidle' });
      await live.evaluate(() => document.fonts.ready);
      for (const expanded of [false, true]) {
        await live.evaluate(open => document.querySelectorAll('main details').forEach(d => d.open = open), expanded);
        const targets = await auditTargetSizes(live);
        assert.deepEqual(targets.failures, [], `${route} @${width}, expanded=${expanded}: touch targets`);
      }
    }
  }
  await live.close();
  console.log('PASS commerce: format-specific prices, discounts, sorting, ratings, dates, expiry, invalid sources and UTM preservation.');
} finally { await browser.close(); }
