import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';

const base = process.env.RECOMMENDATIONS_BASE_URL || 'http://127.0.0.1:4173';
const catalogue = JSON.parse(await fs.readFile('data/reading-catalogue.json', 'utf8'));
const books = catalogue.libros.filter(b => b.estado === 'publicado');
const imported = books.filter(b => b.id.startsWith('isbn-'));
const browser = await chromium.launch({ headless: true });
await fs.mkdir('.ci/reading-intake-browser', { recursive: true });
try {
  const page = await browser.newPage({ viewport: { width: 390, height: 900 }, reducedMotion: 'reduce' });
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.clock.setFixedTime(new Date('2026-10-20T16:00:00Z'));
  await page.goto(base + '/recomendaciones/');
  await page.locator('[data-filter="q"]').waitFor({ state: 'visible' });
  assert.equal(await page.locator('[data-catalogue-book]').count(), books.length);
  for (const b of imported) {
    await page.locator('[data-filter="q"]').fill(b.isbn13);
    // ISBN is a useful lookup as well as title/author.
    assert.equal(await page.locator('[data-catalogue-book]:visible').count(), 1);
    await page.goto(base + '/recomendaciones/libros/' + b.slug + '/');
    assert.equal(await page.locator('main h1').innerText(), b.titulo);
    await page.locator('.catalogue-book-cover').evaluate(img => img.decode());
    // The main button names the edition it sells: «Comprar en Amazon · Tapa dura».
    const search = page.locator('a.catalogue-buy-link');
    assert.match(await search.textContent(), /^Comprar en Amazon(\s|$)/);
    // Straight to the Amazon product when its ASIN is verified; otherwise the ISBN search.
    const buy = new URL(await search.getAttribute('href'));
    if (!buy.pathname.startsWith('/dp/')) assert.equal(buy.searchParams.get('k'), b.isbn13);
    assert.equal(buy.searchParams.get('tag'), 'davidporto-21');
    assert.match(await search.getAttribute('rel'), /sponsored/);
    assert.equal(await page.locator('.catalogue-cover-panel > a').getAttribute('href'),await search.getAttribute('href'));
    const authors = await page.locator('.catalogue-author a').count();
    assert.equal(authors, b.autores.length);
    const ld = JSON.parse(await page.locator('script[type="application/ld+json"]').first().textContent());
    assert.equal(ld['@graph'].find(x => x['@type'] === 'Book').isbn, b.isbn13);
    assert(!JSON.stringify(ld).includes('aggregateRating'));
    const publisherHref = b.editorial_slug ? '/editoriales/' + b.editorial_slug + '/' : '/recomendaciones/editoriales/' + b.editorial_catalogo_slug + '/';
    assert(await page.locator('main a[href="' + publisherHref + '"]').count(), 'La ficha enlaza a la página de su editorial');
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    await page.goto(base + '/recomendaciones/');
  }
  await page.goto(base + '/mapa-del-sitio/');
  const accordion = page.locator('details.directory-reading-books').first();
  assert.equal(await accordion.getAttribute('open'), null);
  assert.equal(await accordion.locator('a').count(), books.length);
  await accordion.locator('summary').focus(); await page.keyboard.press('Enter');
  assert(await accordion.locator('a').first().isVisible());
  for (const publisher of new Set(imported.filter(b => b.editorial_slug).map(b => b.editorial_slug))) {
    await page.goto(base + '/editoriales/' + publisher + '/');
    const heading = page.getByRole('heading', { name: 'Libros de este sello en el catálogo de lectura' });
    assert(await heading.isVisible());
    assert.equal(await heading.locator('..').locator('ul a').count(), books.filter(b => b.editorial_slug === publisher).length);
  }
  // Calendar boundaries use Madrid's civil day, including the DST change.
  for (const [now, today] of [['2026-10-20T22:30:00Z', '2026-10-21'], ['2026-10-25T23:30:00Z', '2026-10-26']]) {
    const dates = [0, 14, 15, -1].map(n => new Date(Date.parse(today + 'T00:00:00Z') - n * 86400000).toISOString().slice(0, 10));
    const boundary = await browser.newPage();
    await boundary.clock.setFixedTime(new Date(now));
    await boundary.route('**/novelty-test/', route => route.fulfill({ contentType: 'text/html', body: '<main data-reading-catalogue>' + [...dates, '2026-10', '2026', ''].map(s => '<p><span data-release-label="' + s + '" data-release-fallback="Libros recomendados">Libros recomendados</span></p>').join('') + '</main><script src="/assets/reading-catalogue.js?v=6"></script>' }));
    await boundary.goto(base + '/novelty-test/');
    assert.deepEqual(await boundary.locator('[data-release-label]').allTextContents(), ['Novedad', 'Novedad', 'Libros recomendados', 'Próximamente', 'Libros recomendados', 'Libros recomendados', 'Libros recomendados']);
    await boundary.close();
  }
  await page.goto(base + '/recomendaciones/');
  await page.screenshot({ path: '.ci/reading-intake-browser/catalogue-mobile.png', fullPage: true });
  if (imported.length) {
    await page.goto(base + '/recomendaciones/libros/' + imported[0].slug + '/');
    await page.screenshot({ path: '.ci/reading-intake-browser/book-mobile.png', fullPage: true });
  }
  assert.deepEqual(errors, []);
  for (const publisher of new Set(imported.filter(b => b.editorial_catalogo_slug).map(b => b.editorial_catalogo_slug))) {
    await page.goto(base + '/recomendaciones/editoriales/' + publisher + '/');
    assert.equal(await page.locator('h1').count(), 1);
    assert.equal(await page.locator('.catalogue-author-books li').count(), imported.filter(b => b.editorial_catalogo_slug === publisher).length, 'La ficha del sello lista sus libros');
  }
  console.log(`PASS ${imported.length} imported books, ${new Set(imported.map(b => b.editorial_slug || b.editorial_catalogo_slug)).size} publishers, sitemap disclosure, edition identity, author links, Madrid/DST novelty boundaries`);
} finally { await browser.close(); }
