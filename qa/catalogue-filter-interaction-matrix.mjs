import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const browser = await chromium.launch({
  headless: true,
  ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}),
});
let catalogueSize = 0;
let searchLatencyMs = 0;

const normalized = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('es').replace(/,/g, ' ').replace(/\s+/g, ' ').trim();
const dateOnly = value => /^\d{4}-\d{2}-\d{2}$/.test(value || '');

try {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, serviceWorkers: 'block' });
  await context.addInitScript(() => {
    try { localStorage.setItem('nl-popup-ts', String(Date.now())); } catch {}
  });
  await context.route('**/*', route => {
    const url = new URL(route.request().url());
    if (url.origin !== origin) return route.abort();
    if (url.pathname === '/assets/reading-market.json') {
      return route.fulfill({ json: { schema_version: 1, offers: [], ratings: [], sales_ranks: [] } });
    }
    return route.continue();
  });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  const response = await page.goto(`${origin}/recomendaciones/`, { waitUntil: 'domcontentloaded' });
  assert.equal(response?.status(), 200, 'el catálogo debe responder HTTP 200');
  await page.waitForFunction(() => {
    const root = document.querySelector('[data-reading-catalogue]');
    if (root?.dataset.catalogueReady === 'true') return true;
    window.dispatchEvent(new HashChangeEvent('hashchange'));
    return false;
  }, null, { timeout: 60000 });
  await page.waitForFunction(() => !document.querySelector('[data-reading-catalogue]').dataset.facetsPending);

  const model = await page.locator('[data-catalogue-book]').evaluateAll(cards => {
    const monthEnd = month => new Date(Date.UTC(Number(month.slice(0, 4)), Number(month.slice(5)), 0)).toISOString().slice(0, 10);
    return cards.map(card => {
      const d = card.dataset;
      const lower = d.published || (d.publishedMonth ? `${d.publishedMonth}-01` : d.year ? `${d.year}-01-01` : '');
      const upper = d.published || (d.publishedMonth ? monthEnd(d.publishedMonth) : d.year ? `${d.year}-12-31` : '');
      const isbn = d.isbn || card.querySelector('[data-isbn]')?.dataset.isbn || '';
      return {
        id: d.bookId,
        group: d.group || '',
        categories: (d.categories || '').split(' ').filter(Boolean),
        formats: [...new Set([...(d.formats || '').split(' '), ...(d.formatPrices || '').split(' ').map(item => item.split(':')[0])].filter(Boolean))],
        pages: Number(d.pages) || null,
        lower,
        upper,
        published: d.published || '',
        search: d.search || `${d.title} ${d.author} ${isbn}`,
        isbn,
        prices: Object.fromEntries((d.formatPrices || '').split(' ').filter(Boolean).map(item => {
          const [format, cents] = item.split(':');
          return [format, Number(cents)];
        })),
      };
    });
  });
  catalogueSize = model.length;
  assert.ok(model.length > 100, `se esperaban las páginas completas, solo hay ${model.length} libros`);
  const today = await page.evaluate(() => new Intl.DateTimeFormat('sv-SE', {
    timeZone: 'Europe/Madrid', year: 'numeric', month: '2-digit', day: '2-digit',
  }).format(new Date()));
  const day = value => Date.parse(`${value}T00:00:00Z`);
  const isReleased = card => !card.lower || card.lower <= today;
  const visibleIds = () => page.locator('[data-catalogue-book]:visible').evaluateAll(cards => cards.map(card => card.dataset.bookId));
  const resultCount = () => page.locator('[data-catalogue-count]').innerText().then(text => Number(text.match(/^\d+/)?.[0] || 0));
  const hashFor = entries => {
    const params = new URLSearchParams();
    for (const [key, value] of entries) params.append(key, value);
    return `#${params}`;
  };
  const applyHash = async (entries, expected, controls = []) => {
    const hash = hashFor(entries);
    await page.evaluate(value => { location.hash = value; }, hash);
    try {
      await page.waitForFunction(({ entries, controls }) => {
      const root = document.querySelector('[data-reading-catalogue]');
      if (!root) return false;
      const fieldsReady = controls.every(([name, value]) => {
        const field = document.querySelector(`[data-filter="${CSS.escape(name)}"]`);
        return field?.value === value;
      });
      const facetsReady = entries.every(([name, value]) => {
        const boxes = [...document.querySelectorAll('input[data-facet]')].filter(box => box.dataset.facet === name);
        return boxes.length ? boxes.some(box => box.value === value && box.checked) : true;
      });
      return fieldsReady && facetsReady;
      }, { entries, controls }, { timeout: 10000 });
    } catch (error) {
      const debug = await page.evaluate(({ entries, controls }) => ({
        hash: location.hash,
        fields: controls.map(([name]) => [name, document.querySelector(`[data-filter="${CSS.escape(name)}"]`)?.value]),
        facets: entries.map(([name, value]) => [name, value, [...document.querySelectorAll('input[data-facet]')].some(box => box.dataset.facet === name && box.value === value && box.checked)]),
        pending: document.querySelector('[data-reading-catalogue]')?.dataset.facetsPending,
        count: document.querySelector('[data-catalogue-count]')?.textContent,
      }), { entries, controls });
      throw new Error(`${hash}: no se aplicó la URL esperada: ${JSON.stringify(debug)} (${error.message})`);
    }
    assert.equal(await resultCount(), expected, `${hash}: contador de resultados incorrecto`);
    const shown = await visibleIds();
    assert.ok(shown.length <= 24, `${hash}: se muestran ${shown.length} libros en una página`);
    assert.ok(shown.every(id => model.some(card => card.id === id)), `${hash}: tarjeta visible ajena al catálogo`);
    return shown;
  };
  const runSingle = async (key, value, predicate) => {
    const expected = model.filter(predicate).length;
    await applyHash([[key, value]], expected, [[key, value]]);
  };

  // Extensión, estado y novedades: cada valor publicado debe coincidir con los metadatos de las fichas.
  for (const [value, predicate] of [
    ['breve', card => card.pages !== null && card.pages < 200],
    ['media', card => card.pages !== null && card.pages >= 200 && card.pages < 400],
    ['larga', card => card.pages !== null && card.pages >= 400 && card.pages < 600],
    ['muy-larga', card => card.pages !== null && card.pages >= 600],
  ]) {
    await runSingle('paginas', value, card => isReleased(card) && predicate(card));
  }
  await runSingle('estado', 'todos', () => true);
  await runSingle('estado', 'proximos', card => Boolean(card.lower) && card.lower > today);
  assert.equal(await page.locator('[data-filter="novedad"]').count(), 0, 'el selector retirado de novedades no debe reaparecer');

  // Precios estáticos: el límite es inclusivo y queda ligado al formato elegido.
  const priced = model.find(card => isReleased(card) && Object.keys(card.prices).length);
  assert.ok(priced, 'el catálogo debe tener al menos un precio/formato para probar el límite');
  const [priceFormat, cents] = Object.entries(priced.prices)[0];
  const price = (cents / 100).toFixed(2);
  const priceExpected = model.filter(card => isReleased(card) && card.prices[priceFormat] === cents).length;
  await applyHash([
    ['precio_formato', priceFormat], ['precio_min', price], ['precio_max', price],
  ], priceExpected, [['precio_formato', priceFormat], ['precio_min', price], ['precio_max', price]]);

  // Rango inclusivo de fechas, incluyendo fichas cuya publicación solo conoce mes o año.
  const dated = model.filter(card => card.lower && card.upper).sort((a, b) => a.lower.localeCompare(b.lower));
  assert.ok(dated.length > 10, 'faltan fechas para probar el rango');
  const from = dated[Math.floor(dated.length * 0.35)].lower;
  const to = dated[Math.floor(dated.length * 0.65)].upper;
  const dateExpected = model.filter(card => isReleased(card) && card.upper && card.upper >= from && card.lower && card.lower <= to).length;
  await applyHash([['desde', from], ['hasta', to]], dateExpected, [['desde', from], ['hasta', to]]);

  // OR dentro de una faceta: seleccionar dos géneros devuelve la unión, no su intersección.
  const facets = await page.locator('input[data-facet]').evaluateAll(boxes => boxes
    .filter(box => Number(box.closest('label')?.dataset.count) > 0)
    .map(box => ({ key: box.dataset.facet, value: box.value })));
  const facetValues = (card, key) => key === 'grupo' ? [card.group] : key === 'formato' ? card.formats : card.categories;
  let union;
  for (const key of ['genero', 'edad', 'formato', 'grupo']) {
    const values = facets.filter(item => item.key === key).map(item => item.value);
    for (let i = 0; i < values.length && !union; i++) for (let j = i + 1; j < values.length; j++) {
      const expected = model.filter(card => isReleased(card) && [values[i], values[j]].some(value => facetValues(card, key).includes(value))).length;
      if (expected > 0) { union = { key, values: [values[i], values[j]], expected }; break; }
    }
    if (union) break;
  }
  assert.ok(union, 'se necesitan dos opciones con resultados para comprobar la selección múltiple OR');
  await applyHash(union.values.map(value => [union.key, value]), union.expected, []);
  for (const value of union.values) {
    assert.equal(await page.locator(`input[data-facet="${union.key}"][value="${value}"]`).isChecked(), true, `${union.key}=${value}: casilla no marcada`);
  }

  // AND entre facetas: el resultado satisface cada faceta a la vez; hash recargable y casillas sincronizadas.
  const keys = [...new Set(facets.map(item => item.key))];
  let intersection;
  for (let i = 0; i < keys.length && !intersection; i++) for (let j = i + 1; j < keys.length && !intersection; j++) {
    const left = facets.filter(item => item.key === keys[i]), right = facets.filter(item => item.key === keys[j]);
    for (const a of left) for (const b of right) {
      const expected = model.filter(card => isReleased(card) && facetValues(card, a.key).includes(a.value) && facetValues(card, b.key).includes(b.value)).length;
      if (expected > 0 && expected < model.length) { intersection = { a, b, expected }; break; }
    }
  }
  assert.ok(intersection, 'se necesitan dos facetas compatibles para comprobar AND');
  const entries = [[intersection.a.key, intersection.a.value], [intersection.b.key, intersection.b.value]];
  await applyHash(entries, intersection.expected, []);
  assert.equal(await page.locator(`input[data-facet="${intersection.a.key}"][value="${intersection.a.value}"]`).isChecked(), true);
  assert.equal(await page.locator(`input[data-facet="${intersection.b.key}"][value="${intersection.b.value}"]`).isChecked(), true);

  // Tiempo de respuesta de búsqueda sobre el catálogo completo, no solo sobre la primera página.
  await page.locator('[data-catalogue-filters] [type="reset"]').click();
  await page.waitForFunction(() => !location.hash && document.querySelector('[data-filter="q"]').value === '');
  const searchTarget = model.find(card => card.search.trim())?.search.split(/\s+/)[0];
  assert.ok(searchTarget, 'falta texto para medir la búsqueda');
  const searchExpected = model.filter(card => normalized(card.search).includes(normalized(searchTarget))).length;
  const searchStarted = Date.now();
  await page.locator('[data-filter="q"]').fill(searchTarget);
  await page.waitForFunction(({ value, expected }) => document.querySelector('[data-filter="q"]').value === value
    && Number(document.querySelector('[data-catalogue-count]').textContent.match(/^\d+/)?.[0]) === expected, { value: searchTarget, expected: searchExpected });
  searchLatencyMs = Date.now() - searchStarted;
  assert.ok(searchLatencyMs <= 1500, `buscar en ${catalogueSize} libros tardó ${searchLatencyMs} ms (límite: 1500 ms)`);

  // Un clic añade la segunda opción de la misma faceta y conserva la selección visible.
  await page.locator('[data-catalogue-filters] [type="reset"]').click();
  await page.waitForFunction(() => !location.hash && !document.querySelector('[data-reading-catalogue]').dataset.facetsPending);
  const firstBox = page.locator(`input[data-facet="${union.key}"][value="${union.values[0]}"]`);
  const secondBox = page.locator(`input[data-facet="${union.key}"][value="${union.values[1]}"]`);
  await page.locator(`[data-facet-group="${union.key}"]`).evaluate(details => { details.open = true; });
  await firstBox.check();
  await secondBox.check();
  await page.waitForFunction(expected => Number(document.querySelector('[data-catalogue-count]').textContent.match(/^\d+/)?.[0]) === expected, union.expected);
  assert.ok((await visibleIds()).every(id => model.some(card => card.id === id)));
  assert.deepEqual(new URLSearchParams(new URL(page.url()).hash.slice(1)).getAll(union.key), union.values);

  // Búsqueda sin diacríticos e ISBN con etiqueta/separadores.
  const accent = model.find(card => /[áéíóúüñ]/i.test(card.search));
  assert.ok(accent, 'se necesita contenido acentuado para comprobar la búsqueda sin diacríticos');
  const accentQuery = accent.search.match(/\S*[áéíóúüñ]\S*/i)?.[0] || accent.id;
  const normalizedAccentQuery = normalized(accentQuery);
  await runSingle('q', accentQuery.normalize('NFD').replace(/[\u0300-\u036f]/g, ''), card => normalized(card.search).includes(normalizedAccentQuery));
  const withIsbn = model.find(card => /^97[89]\d{10}$/.test(card.isbn));
  assert.ok(withIsbn, 'se necesita un ISBN-13 para comprobar la búsqueda bibliográfica');
  const isbnQuery = `ISBN-13: ${withIsbn.isbn.slice(0, 3)}-${withIsbn.isbn.slice(3, 6)}-${withIsbn.isbn.slice(6, 12)}-${withIsbn.isbn.slice(12)}`;
  await runSingle('q', isbnQuery, card => card.isbn === withIsbn.isbn);

  // Orden ascendente/descendente de páginas mantiene los datos disponibles y deja los desconocidos al final.
  await page.locator('[data-catalogue-filters] [type="reset"]').click();
  await page.waitForFunction(() => !location.hash && document.querySelector('[data-filter="q"]').value === '');
  for (const [order, direction] of [['paginas_asc', 1], ['paginas_desc', -1]]) {
    await page.locator('[data-filter="orden"]').selectOption(order);
    await page.waitForFunction(value => document.querySelector('[data-filter="orden"]').value === value && !document.querySelector('[data-reading-catalogue]').dataset.facetsPending, order);
    const pages = await page.locator('[data-catalogue-book]:visible').evaluateAll(cards => cards.map(card => Number(card.dataset.pages) || null));
    const known = pages.filter(Number.isFinite);
    assert.ok(known.length > 1, `${order}: faltan fichas paginadas para verificar el orden`);
    assert.ok(known.every((value, i) => i === 0 || direction * (value - known[i - 1]) >= 0), `${order}: páginas desordenadas (${known.join(', ')})`);
    assert.ok(pages.slice(known.length).every(value => value === null), `${order}: las fichas sin dato no quedan al final`);
  }

  // Descubrimiento de opciones extensas: expandir/plegar y buscar no altera los resultados.
  await page.locator('[data-catalogue-filters] [type="reset"]').click();
  await page.waitForFunction(() => !location.hash && !document.querySelector('[data-reading-catalogue]').dataset.facetsPending);
  const genre = page.locator('[data-facet-group="genero"]');
  await genre.evaluate(element => { element.open = true; });
  const more = genre.locator('[data-facet-more]');
  const facetState = await genre.evaluate(element => ({
    options: element.querySelectorAll('input[data-facet]').length,
    shown: [...element.querySelectorAll('label[data-count]')].filter(label => !label.hidden).length,
    active: [...element.querySelectorAll('label[data-count]')].filter(label => !label.hidden && !label.classList.contains('is-empty')).length,
    more: element.querySelector('[data-facet-more]')?.outerHTML || '',
    expanded: element.dataset.expanded,
  }));
  const canExpand = await more.isVisible();
  if (canExpand) {
    await more.click();
    assert.equal(await more.getAttribute('aria-expanded'), 'true', '«Ver todas» no expande la lista');
  } else {
    assert.equal(facetState.shown, facetState.active, 'se ocultan opciones que todavía tienen libros');
  }
  const countBefore = await resultCount();
  const finder = genre.locator('[data-facet-search]');
  assert.equal(await finder.count(), 1, 'falta el buscador de la faceta larga');
  const searchableLabel = genre.locator('label[data-count]').first();
  const labelText = (await searchableLabel.innerText()).trim();
  const term = labelText.split(/\s+/)[0];
  await finder.fill(term);
  await page.waitForFunction(() => !document.querySelector('[data-reading-catalogue]').dataset.facetsPending);
  assert.ok(await searchableLabel.isVisible(), `buscar «${term}» oculta su propia opción`);
  const matchingOptions = await genre.locator('label[data-count]:visible').allInnerTexts();
  assert.ok(matchingOptions.length > 0 && matchingOptions.length < facetState.shown, `buscar «${term}» no acota las opciones`);
  assert.ok(matchingOptions.every(text => normalized(text).includes(normalized(term))), `la búsqueda de faceta conserva opciones que no coinciden con «${term}»`);
  assert.equal(await resultCount(), countBefore, 'buscar una opción de faceta aplicó un filtro sin marcarlo');
  await finder.fill('');
  await page.waitForFunction(() => !document.querySelector('[data-reading-catalogue]').dataset.facetsPending);
  if (canExpand) {
    await more.click();
    assert.equal(await more.getAttribute('aria-expanded'), 'false', '«Ver menos» no pliega las opciones');
  }
  assert.deepEqual(errors, [], `errores JavaScript: ${errors.join('; ')}`);
  await context.close();
} finally {
  await browser.close();
}

console.log(`PASS catalogue-filter-interaction-matrix (${catalogueSize} libros; búsqueda ${searchLatencyMs} ms; opciones, combinación, límites y orden)`);
