import { chromium } from 'playwright';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';

const BASE = process.env.RECOMMENDATIONS_BASE_URL || 'http://127.0.0.1:4173';
const OUT = process.env.RECOMMENDATIONS_ARTIFACT_DIR || '.ci/reading-catalogue';
const publicData = JSON.parse(await fs.readFile('data/reading-catalogue.json', 'utf8'));
const realCount = publicData.libros.filter(b => b.estado === 'publicado').length;
await fs.mkdir(OUT, { recursive: true });
const fixturePath = `${OUT}/fixture.json`;
execFileSync(process.env.PYTHON || 'python', ['tests/test-reading-catalogue.py', '--browser-fixture', fixturePath], { stdio: 'inherit' });
const fixture = JSON.parse(await fs.readFile(fixturePath, 'utf8'));
// En móvil (≤900 px) los filtros se pliegan tras «Filtros» (#1004): abrirlos como haría el lector.
const openFilters = async page => { const toggle = page.locator('[data-catalogue-refine-toggle]'); if (await toggle.isVisible() && await toggle.getAttribute('aria-expanded') === 'false') await toggle.click(); };
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  // Full static discovery and a failed enhancement must never hide books or
  // present a page-sized subset as global search results.
  {
    const context = await browser.newContext({ javaScriptEnabled: false });
    const page = await context.newPage();
    await page.goto(`${BASE}/recomendaciones/`);
    const urls = await page.locator('a[data-catalogue-page]').evaluateAll(xs => xs.map(a => a.href));
    const seen = [];
    for (const url of [`${BASE}/recomendaciones/`, ...urls]) {
      await page.goto(url);
      seen.push(...await page.locator('[data-catalogue-book]').evaluateAll(xs => xs.map(x => x.dataset.bookId)));
      assert.equal(await page.locator('link[rel=canonical]').getAttribute('href'), 'https://davidportodiaz.com' + new URL(url).pathname);
    }
    assert.equal(seen.length, realCount);
    assert.equal(new Set(seen).size, realCount);
    await context.close();
  }
  for (const fault of ['unavailable', 'stale']) {
    const context = await browser.newContext();
    await context.addInitScript(() => { localStorage.setItem('nl-popup-ts', String(Date.now())); });
    const page = await context.newPage();
    await page.route('**/recomendaciones/pagina/2/', async route => {
      if (route.request().resourceType() === 'document') return route.continue();
      if (fault === 'unavailable') return route.fulfill({status:503,contentType:'text/html',body:'Unavailable'});
      const response = await route.fetch();
      return route.fulfill({response,body:(await response.text()).replace(/data-catalogue-version="[^"]+"/, 'data-catalogue-version="old"')});
    });
    await page.goto(`${BASE}/recomendaciones/`);
    await page.waitForFunction(() => document.querySelector('[data-catalogue-count]').textContent.includes('No se pudo'));
    assert(await page.locator('[data-catalogue-filters] fieldset').evaluate(el => el.disabled));
    assert(await page.locator('[data-catalogue-static-pagination]').isVisible());
    assert.equal(await page.locator('[data-catalogue-book]:visible').count(), Math.min(realCount,96));
    await page.locator('a[data-catalogue-page]').first().click();
    await page.waitForLoadState('domcontentloaded');
    assert.equal(new URL(page.url()).pathname, '/recomendaciones/pagina/2/');
    assert.equal(await page.locator('[data-reading-catalogue]').count(), 0);
    assert.equal(await page.locator('[data-catalogue-book]').count(), Math.min(realCount - 96,96));
    await context.close();
  }
  // Tras publicar, el navegador puede servir el índice desde caché con la versión anterior y las páginas
  // ya nuevas: se recarga una vez y el catálogo queda completo y filtrable.
  {
    const context = await browser.newContext();
    await context.addInitScript(() => { localStorage.setItem('nl-popup-ts', String(Date.now())); });
    const page = await context.newPage();
    let served = 0;
    await page.route('**/assets/reading-market.json', route => route.fulfill({ status: 404, body: '' }));
    await page.route('**/recomendaciones/', async route => {
      const response = await route.fetch();
      if (served++) return route.fulfill({ response });
      return route.fulfill({ response, body: (await response.text()).replace(/data-catalogue-version="[^"]+"/, 'data-catalogue-version="cached"') });
    });
    await page.goto(`${BASE}/recomendaciones/`);
    await page.waitForSelector('[data-catalogue-filters] fieldset:not([disabled])');
    assert.equal(served, 2);
    assert.equal(await page.locator('[data-catalogue-book]').count(), realCount);
    assert.doesNotMatch(await page.locator('[data-catalogue-count]').innerText(), /No se pudo/);
    // Discount filter over the whole catalogue: 5/10/25/50 % must match the red badges Amazon confirmed (static data only).
    const madrid = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Europe/Madrid' }).format(new Date());
    const best = await page.locator('[data-catalogue-book]').evaluateAll(cards => cards.map(card => Math.max(0, ...[...card.querySelectorAll('[data-offer-checked]')].map(e => Number(e.textContent.replace(/\D/g, ''))))));
    const badges = await page.locator('[data-catalogue-book] [data-offer-checked]').count();
    assert.ok(badges > 0, 'no discount badges rendered');
    for (const checked of await page.locator('[data-offer-checked]').evaluateAll(els => els.map(e => e.dataset.offerChecked))) assert.ok((Date.parse(madrid) - Date.parse(checked)) / 864e5 <= 3, `expired badge ${checked}`);
    await page.locator('[data-filter="estado"]').evaluate(el => { el.value = 'todos'; for (const t of ['input', 'change']) el.dispatchEvent(new Event(t, { bubbles: true })); });
    for (const threshold of [5, 10, 25, 50]) {
      await page.locator('[data-filter="descuento"]').evaluate((el, v) => { el.value = v; for (const t of ['input', 'change']) el.dispatchEvent(new Event(t, { bubbles: true })); }, String(threshold));
      const expected = best.filter(pct => pct >= threshold).length;
      await page.waitForFunction(n => new RegExp('^' + n + ' libros?(?: |$)').test(document.querySelector('[data-catalogue-count]').textContent) || (n === 0 && !document.querySelector('[data-catalogue-empty]').hidden), expected);
      console.log(`descuento >= ${threshold} %: ${expected} libros`);
    }
    // «Prime Day y Black Friday» (Temporada) = current Amazon offers of 10 % or more.
    await page.locator('[data-filter="descuento"]').evaluate(el => { el.value = ''; for (const t of ['input', 'change']) el.dispatchEvent(new Event(t, { bubbles: true })); });
    await page.locator('[data-facet="temporada"][value="ofertas-amazon"]').evaluate(el => { el.checked = true; for (const t of ['input', 'change']) el.dispatchEvent(new Event(t, { bubbles: true })); });
    const primeDay = best.filter(pct => pct >= 10).length;
    await page.waitForFunction(n => new RegExp('^' + n + ' libros?(?: |$)').test(document.querySelector('[data-catalogue-count]').textContent), primeDay);
    console.log(`temporada Prime Day: ${primeDay} libros`);
    await context.close();
  }
  for (const width of [320, 390, 768, 1024, 1440]) {
    const context = await browser.newContext({ viewport: { width, height: 1000 }, reducedMotion: 'reduce' });
    // El popup de newsletter se abre por temporizador en /cuaderno/ y tapa el clic en runners lentos.
    await context.addInitScript(() => { try { localStorage.setItem('nl-popup-ts', String(Date.now())); } catch {} });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto(`${BASE}/recomendaciones/`);
    await page.waitForSelector('[data-catalogue-filters] fieldset:not([disabled])');
    await openFilters(page);
    assert.match(await page.locator('h1').innerText(), /Libros recomendados/);
    assert.equal(await page.locator('[data-catalogue-book]').count(), realCount);
    assert(await page.locator('[data-catalogue-empty]').isHidden());
    assert.deepEqual(await page.locator('.section-context__links a').allInnerTexts(), ['Catálogo', 'Autores', 'Editoriales', 'Atlas literario', 'Concursos']);
    await page.locator('details[data-facet-group="genero"]').evaluate(d => { d.open = true; });
    // Solo se ofrecen categorías con libros publicados: ninguna casilla muerta.
    const offered = await page.locator('input[data-facet="genero"]').evaluateAll(xs => xs.map(x => x.value));
    const counts = await page.locator('[data-catalogue-book]').evaluateAll(xs => xs.map(x => x.dataset.categories || '').join(' ').split(/\s+/));
    assert.deepEqual(offered.filter(v => !counts.includes(v)), [], 'Categorías ofrecidas sin libros');
    // Romantasy (romance + fantasía) se deriva y aparece en cuanto hay libros de ambos géneros.
    assert.equal(await page.locator('input[data-facet="genero"][value="romantasy"]').count(), counts.includes('romantasy') ? 1 : 0);
    // Con un tipo de libro elegido, los géneros sin resultados bajan al final y quedan desactivados.
    await page.locator('input[data-facet="grupo"][value="novela"]').check();
    const genreState = await page.locator('details[data-facet-group="genero"] input[data-facet]').evaluateAll(xs => xs.map(x => x.disabled));
    assert(genreState.includes(true) && genreState.indexOf(true) > 0 && genreState.slice(genreState.indexOf(true)).every(Boolean), 'Las opciones vacías van al final');
    await page.locator('input[data-facet="grupo"][value="novela"]').uncheck();
    await page.locator('input[data-facet="grupo"][value="cocina"]').check();
    await page.getByRole('button', { name: 'Restablecer' }).click();
    assert.equal(await page.locator('input[data-facet]:checked').count(), 0);
    await page.waitForFunction(n => document.querySelectorAll('[data-catalogue-book]:not([hidden])').length === Math.min(n,24), realCount);
    assert.equal(await page.locator('[data-catalogue-book]:visible').count(), Math.min(realCount,24));
    await page.getByRole('button', { name: 'Buscar libros', exact: true }).focus();
    await page.keyboard.press('Enter');
    assert.equal(await page.locator('[data-catalogue-book]:visible').count(), Math.min(realCount,24));
    await page.waitForFunction(() => document.documentElement.scrollWidth <= innerWidth + 1);
    await page.evaluate(() => { document.activeElement?.blur(); window.scrollTo({ top: 0, behavior: 'instant' }); });
    await page.waitForFunction(() => window.scrollY === 0);
    await page.screenshot({ path: `${OUT}/catalogue-${width}.png`, fullPage: true });
    await page.goto(`${BASE}/cuaderno/`);
    assert.equal(await page.locator('.cuaderno-feature h2 a, .cuaderno-entry h3 a').count(), 8);
    // On mobile the reachable link lives in a closed footer <details>: open it as a reader would.
    await page.locator('footer.site-footer details.ft-group').filter({ has: page.locator('a[href="/recomendaciones/"]') }).first().locator('summary').click();
    await page.getByRole('link', { name: 'Libros recomendados', exact: true }).first().click();
    assert.equal(new URL(page.url()).pathname, '/recomendaciones/');
    assert.deepEqual(errors, []);
    await context.close();
  }
  // ISBN-13 con separadores: mismas fichas y conservación de la consulta original.
  {
    const context = await browser.newContext({ viewport: { width: 390, height: 900 } });
    const page = await context.newPage();
    await page.goto(`${BASE}/recomendaciones/`);
    await page.waitForSelector('[data-catalogue-filters] fieldset:not([disabled])');
    const query = page.locator('[data-filter="q"]');
    const setQuery = async value => {
      await query.fill(value);
      await page.waitForFunction(q => new URLSearchParams(location.hash.slice(1)).get('q') === q, value);
    };
    const visibleIds = () => page.locator('[data-catalogue-book]:visible').evaluateAll(nodes => nodes.map(node => node.dataset.bookId).sort());
    await setQuery('9791388092268');
    const expected = await visibleIds();
    assert(expected.includes('isbn-9791388092268'), 'El ISBN original debe encontrar Ponte fino');
    for (const value of ['979-13-8809-226-8', '979 13 8809 226 8', 'ISBN 979-13-8809-226-8', 'ISBN-13: 979-13-8809-226-8']) {
      await setQuery(value);
      assert.deepEqual(await visibleIds(), expected, `Resultados distintos para ${value}`);
    }
    const persisted = 'ISBN 979-13-8809-226-8';
    await setQuery(persisted);
    assert.equal(new URLSearchParams(new URL(page.url()).hash.slice(1)).get('q'), persisted);
    await page.reload();
    await page.waitForSelector('[data-catalogue-filters] fieldset:not([disabled])');
    assert.equal(await query.inputValue(), persisted);
    assert.deepEqual(await visibleIds(), expected);
    await setQuery('9790000000000');
    assert.deepEqual(await visibleIds(), []);
    assert(await page.locator('[data-catalogue-empty]').isVisible());
    await setQuery('1984');
    assert((await visibleIds()).includes('isbn-9788491058298'));
    await setQuery('La hipótesis más peligrosa');
    const accented = await visibleIds();
    assert(accented.includes('isbn-9791387846008'));
    await setQuery('La hipotesis mas peligrosa');
    assert.deepEqual(await visibleIds(), accented);
    await setQuery('Martín Berasategui');
    const author = await visibleIds();
    assert(author.includes('isbn-9791388092268'));
    await setQuery('Martin Berasategui');
    assert.deepEqual(await visibleIds(), author);
    const multipleAuthors = publicData.libros.find(b => b.estado === 'publicado' && b.autores.length > 1);
    assert(multipleAuthors, 'Debe probarse una ficha con varios autores');
    await setQuery(multipleAuthors.autores.join(' '));
    assert((await visibleIds()).includes(multipleAuthors.id), 'La búsqueda debe conservar todos los autores sin duplicarlos en data-search');
    await setQuery(multipleAuthors.autores.join(', '));
    assert((await visibleIds()).includes(multipleAuthors.id), 'Las comas entre autores no deben impedir la búsqueda');
    await context.close();
  }
  // Real pilot: same purchase component and optional sections as other books.
  {
    const context = await browser.newContext({ viewport: { width: 390, height: 900 } });
    const page = await context.newPage();
    await page.goto(`${BASE}/recomendaciones/libros/coraline/`);
    assert.equal(await page.locator('main h1').innerText(), 'Coraline');
    await page.locator('.catalogue-book-cover').evaluate(img => img.decode());
    const coverLink = page.locator('.catalogue-cover-panel > a');
    assert.equal(await coverLink.getAttribute('href'), await page.locator('a[data-purchase-format="tapa-blanda"]').getAttribute('href'));
    assert.match(await coverLink.getAttribute('rel'), /sponsored/);
    await coverLink.focus();
    assert(await coverLink.evaluate(a => a === document.activeElement));
    assert.equal(await page.locator('[data-purchase-format]').count(), 4);
    assert.equal(await page.locator('audio,[data-catalogue-speak],.catalogue-fragment').count(), 0, 'No non-scalable audio or sample UI');
    const reviews = page.locator('details').filter({ has: page.locator('summary', { hasText: 'Opiniones y referencias externas' }) });
    assert.equal(await reviews.getAttribute('open'), null);
    await reviews.locator('summary').click();
    assert(await reviews.locator('a').first().isVisible());
    assert(!/Voz sintética|Esta comprobación no implica|compras adscritas/.test(await page.locator('main').innerText()));
    await page.screenshot({ path: `${OUT}/coraline-mobile.png`, fullPage: true });
    await context.close();
  }
  // Large text and custom spacing must preserve all content on narrow screens.
  for (const width of [320, 390, 768]) {
    const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    for (const route of ['/recomendaciones/', '/recomendaciones/libros/coraline/', '/recomendaciones/autores/neil-gaiman/']) {
      for (const css of ['html{font-size:200%!important}', '*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}', 'html{font-size:200%!important}*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}']) {
        await page.goto(`${BASE}${route}`);
        await page.addStyleTag({ content: css });
        await page.evaluate(() => document.fonts.ready);
        const overflow = await page.locator('main *').evaluateAll(nodes => nodes.flatMap(node => {
          const r = node.getBoundingClientRect(), s = getComputedStyle(node);
          return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && (r.right > innerWidth + 1 || r.left < -1) ? [{ tag: node.tagName, class: node.className, right: r.right, left: r.left }] : [];
        }));
        assert.deepEqual(overflow, [], `${route} @ ${width}: ${css}`);
      }
    }
    await context.close();
  }
  // Rendered data uses intercepted, isolated fixtures; no synthetic books on the site.
  const context = await browser.newContext({ viewport: { width: 390, height: 900 }, reducedMotion: 'reduce' });
  await context.route('**/recomendaciones/', route => route.fulfill({ contentType: 'text/html; charset=utf-8', body: fixture.hub }));
  await context.route('**/recomendaciones/libros/contrato-uno/', route => route.fulfill({ contentType: 'text/html; charset=utf-8', body: fixture.book }));
  await context.route('**/assets/reading-covers/*.png', route => route.fulfill({ contentType: 'image/png', body: Buffer.from(fixture.cover, 'base64') }));
  const page = await context.newPage();
  await page.clock.install({ time: new Date('2026-10-20T12:00:00Z') });
  await page.goto(`${BASE}/recomendaciones/`);
  assert.equal(await page.locator('[data-catalogue-book]:visible').count(), 2);
  await openFilters(page);
  await page.locator('details[data-facet-group="genero"]').evaluate(d => { d.open = true; }); await page.locator('details[data-facet-group="temporada"]').evaluate(d => { d.open = true; }); await page.locator('input[data-facet="genero"][value="romantasy"]').check();
  await page.locator('input[data-facet="temporada"][value="halloween"]').check();
  assert.equal(await page.locator('[data-catalogue-book]:visible').count(), 1);
  const href = await page.locator('[data-catalogue-book]:visible .catalogue-card__ficha').getAttribute('href');
  await page.locator('input[data-facet="genero"][value="romantasy"]').uncheck(); await page.locator('input[data-facet="genero"][value="fantasia"]').check();
  assert.equal(await page.locator('[data-catalogue-book]:visible .catalogue-card__ficha').getAttribute('href'), href);
  await page.locator('[data-filter="q"]').fill('TITULO');
  await page.locator('[data-filter="q"]').press('Enter');
  assert.equal(await page.locator('[data-catalogue-book]:visible').count(), 1);
  await page.reload();
  assert.equal(await page.locator('[data-filter="q"]').inputValue(), 'TITULO');
  await openFilters(page);
  await page.getByRole('button', { name: 'Restablecer' }).click();
  await page.locator('[data-filter="novedad"]').selectOption('180');
  assert.equal(await page.locator('[data-catalogue-book]:visible').count(), 1);
  await page.clock.setSystemTime(new Date('2027-10-20T12:00:00Z'));
  await page.evaluate(() => window.dispatchEvent(new Event('pageshow')));
  assert.equal(await page.locator('[data-catalogue-book]:visible').count(), 0);
  await page.getByRole('button', { name: 'Restablecer' }).click();
  await page.locator('[data-filter="q"]').fill('zzzz');
  assert.equal(await page.locator('[data-catalogue-book]:visible').count(), 0);
  assert(await page.locator('[data-catalogue-empty]').isVisible());
  await page.goto(`${BASE}${href}`);
  assert.equal(await page.locator('link[rel="canonical"]').getAttribute('href'), `https://davidportodiaz.com${href}`);
  assert.equal(await page.locator('main h1').innerText(), 'Título de prueba técnica');
  await page.locator('.catalogue-book-cover').evaluate(img => img.decode());
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
  await page.screenshot({ path: `${OUT}/book-fixture-mobile.png`, fullPage: true });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.screenshot({ path: `${OUT}/book-fixture-desktop.png`, fullPage: true });
  await page.reload();
  assert.equal(await page.locator('[data-catalogue-speak],audio,.catalogue-fragment').count(),0);
  await context.close();
  const nojs = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 390, height: 900 } });
  const staticPage = await nojs.newPage();
  await staticPage.goto(`${BASE}/recomendaciones/`);
  assert(await staticPage.locator('[data-catalogue-book] h3 a').first().isVisible());
  assert(await staticPage.locator('input[data-facet="genero"]').first().isDisabled());
  await nojs.route('**/recomendaciones/', route => route.fulfill({ contentType: 'text/html; charset=utf-8', body: fixture.hub }));
  await staticPage.reload();
  assert.equal(await staticPage.locator('[data-catalogue-book]').count(), 2);
  assert.equal(await staticPage.locator('[data-catalogue-book] .catalogue-card__ficha').first().getAttribute('href'), href);
  await nojs.close();
  console.log('PASS catálogo navegador: 5 tamaños, vacío real, filtros combinados, URL única, teclado, novedades, fichas y sin JS.');
} finally {
  await browser.close();
}
