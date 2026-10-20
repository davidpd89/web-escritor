import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { auditTargetSizes } from './target-size-audit.mjs';

const base = process.env.RECOMMENDATIONS_BASE_URL || 'http://127.0.0.1:4173';
await fs.mkdir('.ci/reading-commerce', { recursive: true });
execFileSync(process.env.PYTHON || 'python', ['tests/test-reading-catalogue.py', '--browser-fixture', '.ci/reading-commerce/fixture.json']);
const fixture = JSON.parse(await fs.readFile('.ci/reading-commerce/fixture.json', 'utf8'));
const browser = await chromium.launch({ headless: true });
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
  const open = async () => { await page.goto(`${base}/recomendaciones/?utm_source=prueba`); await field('precio_max').waitFor({ state: 'attached' }); await page.waitForFunction(() => !document.querySelector('[data-filter="precio_max"]').disabled); await page.locator('form details summary').click(); };
  await open();
  await field('formato').selectOption('tapa-dura'); await field('precio_max').fill('10');
  assert.deepEqual(await ids(), [], 'A hardcover must not inherit its cheaper ebook price');
  await field('formato').selectOption('ebook'); assert.deepEqual(await ids(), ['contrato-uno']);
  await field('descuento').selectOption('50'); assert.deepEqual(await ids(), ['contrato-uno']);
  await field('precio_min').fill('6'); assert.deepEqual(await ids(), []);
  await page.getByRole('button', { name: 'Restablecer' }).click();
  await page.waitForFunction(() => document.querySelector('[data-catalogue-count]').textContent === '2 libros');
  assert.equal(new URL(page.url()).searchParams.get('utm_source'), 'prueba');
  await field('orden').selectOption('precio_asc'); assert.deepEqual(await ids(), ['contrato-uno', 'contrato-dos']);
  await field('orden').selectOption('precio_desc'); assert.deepEqual(await ids(), ['contrato-dos', 'contrato-uno']);
  await field('orden').selectOption('titulo'); assert.deepEqual(await ids(), ['contrato-dos', 'contrato-uno']);
  await field('orden').selectOption('titulo_desc'); assert.deepEqual(await ids(), ['contrato-uno', 'contrato-dos']);
  await field('valoracion').selectOption('4'); assert.deepEqual(await ids(), ['contrato-uno']);
  await field('valoracion').selectOption('4.5'); assert.deepEqual(await ids(), []);
  await field('valoracion').selectOption(''); await field('hasta').fill('1990-12-31'); assert.deepEqual(await ids(), ['contrato-dos']);
  await field('hasta').fill('');
  await page.clock.fastForward(25 * 3600000);
  await page.evaluate(() => window.dispatchEvent(new Event('pageshow')));
  assert(await field('precio_max').isDisabled());
  assert.equal(await page.locator('[data-price-book]:not([hidden])').count(), 0);
  market = { schema_version: 1, offers: [offer('contrato-uno', 'ebook', 1, { moneda: 'USD' }), offer('contrato-dos', 'ebook', 1, { url: 'https://amazon.es.evil.invalid/dp/B000000001?tag=contrato-21' }), offer('contrato-uno', 'ebook', 1, { actualizado_en: '2027-01-01T00:00:00Z', caduca_en: '2027-01-02T00:00:00Z' })], ratings: [{ ...payload.ratings[0], puntuacion: 6 }] };
  await page.goto(`${base}/recomendaciones/?utm_source=prueba`); await page.waitForLoadState('networkidle');
  assert(await field('precio_max').isDisabled()); assert(await field('valoracion').isDisabled());
  assert.equal(await page.locator('[data-price-book]:not([hidden])').count(), 0);
  assert.equal(await page.locator('[data-rating-book] a').count(), 0);
  assert.deepEqual(errors, []);
  await context.close();
  const live = await browser.newPage({ viewport: { width: 390, height: 900 } });
  await live.route('**/assets/reading-market.json', route => route.fulfill({ json: { schema_version: 1, offers: [], ratings: [{ ...payload.ratings[0], libro_id: 'lib-0001', actualizado_en: new Date(Date.now() - 3600000).toISOString(), caduca_en: new Date(Date.now() + 3600000).toISOString() }] } }));
  await live.goto(`${base}/`);
  assert.deepEqual(await live.locator('#masthead-submenu-notebook-hub a').allTextContents(), ['Archivo', 'Libros recomendados']);
  await live.goto(`${base}/recomendaciones/libros/coraline/`);
  const ratingLink = live.locator('[data-rating-book] a');
  await ratingLink.waitFor();
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
  assert.equal(await live.locator('a[href="https://es.wikipedia.org/wiki/Neil_Gaiman"]').count(), 1);
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
