// Paseo aleatorio por filtros y paginación del catálogo: combina facetas, estado, extensión y página al azar
// (semilla reproducible) y comprueba invariantes contra un modelo independiente sacado de las fichas:
//   - el contador coincide con el modelo (OR dentro de una faceta, AND entre facetas);
//   - páginas = ceil(n / 24), la página pedida se acota a [1, páginas] y la URL lo refleja;
//   - la página visible tiene min(24, resto) tarjetas, todas del conjunto esperado;
//   - abrir la misma URL en otra pestaña reproduce exactamente la misma vista.
// Las matrices fijas (catalogue-filter-*.mjs) prueban casos conocidos; este busca los que nadie pensó.
// Reproducir un fallo: QA_SEED=<semilla impresa> node qa/catalogue-random-walk.mjs
import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const seed = Number(process.env.QA_SEED) || (Date.now() % 2147483647);
const steps = Number(process.env.QA_WALK_STEPS) || 40;
const PAGE_SIZE = 24;
console.log(`catalogue-random-walk: semilla ${seed}, ${steps} pasos`);

// mulberry32: determinista para reproducir el mismo paseo con la misma semilla.
let state = seed >>> 0;
const rand = () => { state = (state + 0x6D2B79F5) >>> 0; let t = state; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
const pick = items => items[Math.floor(rand() * items.length)];
const sample = (items, k) => [...items].sort(() => rand() - 0.5).slice(0, k);

const browser = await chromium.launch({
  headless: true,
  ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}),
});
const log = [];
try {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, serviceWorkers: 'block' });
  await context.addInitScript(() => { try { localStorage.setItem('nl-popup-ts', String(Date.now())); } catch {} });
  await context.route('**/*', route => {
    const url = new URL(route.request().url());
    if (url.origin !== origin) return route.abort();
    if (url.pathname === '/assets/reading-market.json') return route.fulfill({ json: { schema_version: 1, offers: [], ratings: [], sales_ranks: [] } });
    return route.continue();
  });
  const errors = [];
  const open = async hash => {
    const page = await context.newPage();
    page.on('pageerror', error => errors.push(error.message));
    const response = await page.goto(`${origin}/recomendaciones/${hash}`, { waitUntil: 'domcontentloaded' });
    assert.equal(response?.status(), 200, 'el catálogo debe responder HTTP 200');
    await page.waitForFunction(() => {
      const root = document.querySelector('[data-reading-catalogue]');
      if (root?.dataset.catalogueReady === 'true') return !root.dataset.facetsPending;
      window.dispatchEvent(new HashChangeEvent('hashchange'));
      return false;
    }, null, { timeout: 60000 });
    return page;
  };
  const page = await open('');
  const model = await page.locator('[data-catalogue-book]').evaluateAll(cards => cards.map(card => {
    const d = card.dataset;
    return {
      id: d.bookId,
      group: d.group || '',
      categories: (d.categories || '').split(' ').filter(Boolean),
      formats: [...new Set([...(d.formats || '').split(' '), ...(d.formatPrices || '').split(' ').map(item => item.split(':')[0])].filter(Boolean))],
      pages: Number(d.pages) || null,
      lower: d.published || (d.publishedMonth ? `${d.publishedMonth}-01` : d.year ? `${d.year}-01-01` : ''),
    };
  }));
  assert.ok(model.length > 100, `se esperaba el catálogo completo, solo hay ${model.length} libros`);
  const today = await page.evaluate(() => new Intl.DateTimeFormat('sv-SE', { timeZone: 'Europe/Madrid', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date()));
  const released = card => !card.lower || card.lower <= today;
  const facetValues = (card, key) => key === 'grupo' ? [card.group] : key === 'formato' ? card.formats : card.categories;
  const facets = await page.locator('input[data-facet]').evaluateAll(boxes => boxes.map(box => ({ key: box.dataset.facet, value: box.value })));
  const facetKeys = [...new Set(facets.map(item => item.key))];
  assert.ok(facetKeys.length >= 2, 'faltan facetas para el paseo aleatorio');
  const lengths = {
    breve: p => p !== null && p < 200, media: p => p !== null && p >= 200 && p < 400,
    larga: p => p !== null && p >= 400 && p < 600, 'muy-larga': p => p !== null && p >= 600,
  };
  const estados = { '': released, todos: () => true, proximos: card => Boolean(card.lower) && card.lower > today };

  const view = target => target.evaluate(() => ({
    hash: location.hash,
    pagina: new URLSearchParams(location.hash.slice(1)).get('pagina'),
    count: Number(document.querySelector('[data-catalogue-count]')?.textContent.match(/^\d+/)?.[0] ?? -1),
    nav: document.querySelector('[data-catalogue-pagination]')?.textContent || '',
    ids: [...document.querySelectorAll('[data-catalogue-book]')].filter(card => card.checkVisibility()).map(card => card.dataset.bookId),
  }));

  for (let step = 1; step <= steps; step++) {
    // Estado aleatorio: 0-3 facetas con 1-2 valores, a veces estado y extensión, y una página cualquiera.
    const entries = [];
    const chosen = sample(facetKeys, Math.floor(rand() * 4));
    for (const key of chosen) for (const value of sample(facets.filter(f => f.key === key).map(f => f.value), 1 + Math.floor(rand() * 2))) entries.push([key, value]);
    const estado = rand() < 0.3 ? pick(['todos', 'proximos']) : '';
    if (estado) entries.push(['estado', estado]);
    const extension = rand() < 0.25 ? pick(Object.keys(lengths)) : '';
    if (extension) entries.push(['paginas', extension]);
    const expected = model.filter(card => estados[estado](card)
      && (!extension || lengths[extension](card.pages))
      && chosen.every(key => entries.filter(([k]) => k === key).some(([, v]) => facetValues(card, key).includes(v))));
    const total = Math.max(1, Math.ceil(expected.length / PAGE_SIZE));
    const asked = pick([null, 2, total, total + 1, 100000, 1 + Math.floor(rand() * total)]);
    if (asked && asked !== 1) entries.push(['pagina', String(asked)]);
    const shown = Math.min(Math.max(asked || 1, 1), total);
    const params = new URLSearchParams(entries);
    const hash = params.size ? `#${params}` : '';
    const label = `paso ${step} (semilla ${seed}) ${hash || '(sin filtros)'}`;
    log.push(label);

    const current = await page.evaluate(() => location.hash);
    if (current === hash) continue;
    await page.evaluate(value => { location.hash = value || '#'; }, hash);
    try {
      await page.waitForFunction(({ n, shown, total }) => {
        const root = document.querySelector('[data-reading-catalogue]');
        const count = Number(document.querySelector('[data-catalogue-count]')?.textContent.match(/^\d+/)?.[0] ?? -1);
        const nav = document.querySelector('[data-catalogue-pagination]')?.textContent || '';
        return !root.dataset.facetsPending && count === n && (total === 1 || nav.includes(`Página ${shown} de ${total}`));
      }, { n: expected.length, shown, total }, { timeout: 10000 });
    } catch {
      const got = await view(page);
      throw new Error(`${label}: esperaba ${expected.length} libros, página ${shown} de ${total}; la vista dice ${got.count} y «${got.nav.trim().slice(0, 80)}» (${got.hash})`);
    }
    const got = await view(page);
    const wantSize = expected.length ? Math.min(PAGE_SIZE, expected.length - PAGE_SIZE * (shown - 1)) : 0;
    assert.equal(got.ids.length, wantSize, `${label}: ${got.ids.length} tarjetas visibles en la página ${shown} (esperadas ${wantSize})`);
    const allowed = new Set(expected.map(card => card.id));
    const stray = got.ids.filter(id => !allowed.has(id));
    assert.deepEqual(stray, [], `${label}: tarjetas que no cumplen el filtro`);
    assert.equal(new Set(got.ids).size, got.ids.length, `${label}: tarjeta repetida en la página`);
    assert.equal(got.pagina, shown > 1 ? String(shown) : null, `${label}: la URL dice pagina=${got.pagina} y se ve la ${shown}`);

    // Cada 8 pasos, la URL compartida reproduce exactamente la misma vista en otra pestaña.
    if (step % 8 === 0 && got.hash) {
      const twin = await open(got.hash);
      const again = await view(twin);
      assert.deepEqual([again.count, again.pagina, again.ids], [got.count, got.pagina, got.ids], `${label}: recargar ${got.hash} no reproduce la vista`);
      await twin.close();
    }
  }
  assert.deepEqual(errors, [], 'errores de JavaScript durante el paseo');
  console.log(`PASS catalogue-random-walk: ${steps} pasos sobre ${model.length} libros (semilla ${seed})`);
} catch (error) {
  console.error(log.slice(-5).join('\n'));
  throw error;
} finally {
  await browser.close();
}
