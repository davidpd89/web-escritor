import assert from 'node:assert/strict';
import { chromium } from 'playwright';

// Confianza editorial de las valoraciones (#1005): sin una valoración verificada vigente el
// catálogo no pinta una nota. En main, 62 de 88 tarjetas mostraban «Goodreads ★★★★★ 0,0 (0)»
// con el aria-label «aún sin valoraciones públicas», un hecho que el catálogo no conoce.
const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const now = Date.parse('2026-10-30T12:00:00Z');
const iso = ms => new Date(ms).toISOString().replace('.000Z', 'Z');
const dated = { actualizado_en: iso(now - 3600000), caduca_en: iso(now + 72 * 3600000) };
const stale = { actualizado_en: iso(now - 200 * 3600000), caduca_en: iso(now - 32 * 3600000) };
const gr = id => `https://www.goodreads.com/book/show/${id}`;
const browser = await chromium.launch({ headless: true });

async function open(market, { width = 1280, javaScriptEnabled = true } = {}) {
  const context = await browser.newContext({ viewport: { width, height: 900 }, javaScriptEnabled });
  const external = [];
  await context.route('**/*', route => {
    const u = new URL(route.request().url());
    if (u.origin !== origin) { external.push(u.href); return route.abort(); }
    if (u.pathname === '/assets/reading-market.json') return market === 'fail' ? route.fulfill({ status: 503, body: 'down' }) : route.fulfill({ json: market });
    return route.continue();
  });
  const page = await context.newPage();
  if (javaScriptEnabled) await page.clock.install({ time: now });
  await page.goto(`${origin}/recomendaciones/#orden=titulo`, { waitUntil: 'networkidle' });
  return { context, page, external };
}
const boxes = page => page.locator('[data-rating-book]').evaluateAll(list => list.map(box => {
  const a = box.querySelector('a');
  return { id: box.dataset.ratingBook, card: Boolean(box.closest('.catalogue-card')), hidden: box.hidden, isbn: box.dataset.isbn || '', text: box.textContent.replace(/\s+/g, ' ').trim(), state: a?.dataset.ratingState || '', label: a?.getAttribute('aria-label') ?? null, href: a?.href || '', stars: Boolean(box.querySelector('.catalogue-stars')), fill: box.querySelector('.catalogue-stars')?.style.getPropertyValue('--rating') || '' };
}));
const unverifiedOk = (b, where) => {
  assert.doesNotMatch(b.text, /0,0|\(0\)|★/, `${where}: ${b.id} pinta una nota sin verificar: «${b.text}»`);
  assert.equal(b.stars, false, `${where}: ${b.id} pinta estrellas sin valoración verificada`);
  assert.equal(b.label, null, `${where}: ${b.id} lleva un aria-label distinto del texto visible`);
  assert.doesNotMatch(b.text, /sin valoraciones/i, `${where}: ${b.id} afirma que la fuente no tiene opiniones`);
};

try {
  // 1. Proveedor caído (503) y mercado vacío: ninguna tarjeta muestra nota; con ISBN queda un enlace neutro.
  for (const market of ['fail', { schema_version: 1, offers: [], ratings: [] }]) {
    const { context, page, external } = await open(market);
    const all = await boxes(page);
    assert.ok(all.length > 20, 'el catálogo debe tener tarjetas con valoración');
    for (const b of all) {
      unverifiedOk(b, market === 'fail' ? 'proveedor caído' : 'sin dato');
      if (b.card) {
        // En la tarjeta, sin nota no se pinta nada: el enlace neutro era ruido en la cuadrícula.
        assert.equal(b.text, '', `${b.id}: la tarjeta no muestra texto sin valoración`);
        assert.equal(b.hidden, true, `${b.id}: la caja vacía no reserva altura`);
      } else if (b.isbn.length === 13) {
        assert.equal(b.text, 'Goodreads · consultar ficha');
        assert.equal(b.state, 'unavailable');
        assert.equal(b.href, `https://www.goodreads.com/book/isbn/${b.isbn}`);
      } else assert.equal(b.text, '', `${b.id}: sin ISBN no hay enlace que ofrecer`);
    }
    assert.equal(await page.locator('[data-filter="valoracion"]').isDisabled(), true, 'sin valoraciones verificadas el filtro no se ofrece');
    assert.deepEqual(external, [], 'no se piden recursos externos');
    await context.close();
  }

  // 2. Estados mezclados sobre tarjetas reales.
  const ids = await (async () => { const { context, page } = await open({ schema_version: 1, offers: [], ratings: [] }); const all = await boxes(page); await context.close(); return all.filter(b => b.isbn.length === 13).slice(0, 6).map(b => b.id); })();
  const [verified, thin, oneVote, expired, forged, none] = ids;
  const market = { schema_version: 1, offers: [], ratings: [
    { ...dated, libro_id: verified, fuente: 'goodreads', puntuacion: 4.2, numero_valoraciones: 12345, url: gr(101) },
    { ...dated, libro_id: thin, fuente: 'goodreads', puntuacion: 5, numero_valoraciones: 4, url: gr(102) },
    { ...dated, libro_id: oneVote, fuente: 'hardcover', puntuacion: 1, numero_valoraciones: 1, url: 'https://hardcover.app/books/qa-uno' },
    { ...stale, libro_id: expired, fuente: 'goodreads', puntuacion: 4.8, numero_valoraciones: 900, url: gr(104) },
    { ...dated, libro_id: forged, fuente: 'goodreads', puntuacion: 4.9, numero_valoraciones: 700, url: 'https://goodreads.com.evil.invalid/book/show/1' },
  ] };
  for (const width of [390, 768, 1280]) {
    const { context, page, external } = await open(market, { width });
    const by = Object.fromEntries((await boxes(page)).map(b => [b.id, b]));
    // ≥5 opiniones vigentes: nota, recuento y estrellas; nombre accesible = texto visible.
    assert.equal(by[verified].state, 'verified');
    assert.equal(by[verified].text, 'Goodreads ★★★★★ 4,2 (12.345)');
    assert.equal(Math.round(parseFloat(by[verified].fill)), 84);
    assert.equal(by[verified].label, null);
    // 1–4 opiniones: se dice que la muestra es pequeña, sin nota y con su propia fuente.
    for (const [id, text, href] of [[thin, 'Goodreads · menos de 5 valoraciones', gr(102)], [oneVote, 'Hardcover · menos de 5 valoraciones', 'https://hardcover.app/books/qa-uno']]) {
      unverifiedOk(by[id], `${width}px muestra pequeña`);
      assert.equal(by[id].state, 'insufficient');
      assert.equal(by[id].text, text);
      assert.equal(by[id].href, href);
    }
    // Caducado, fuente falsificada y sin dato: la tarjeta no pinta nada.
    for (const id of [expired, forged, none]) {
      unverifiedOk(by[id], `${width}px ${id}`);
      assert.equal(by[id].card, true);
      assert.equal(by[id].text, '');
      assert.equal(by[id].hidden, true);
    }
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    assert.ok(overflow <= 0, `${width}px: scroll horizontal de ${overflow} px`);
    assert.deepEqual(external, []);
    await context.close();
  }

  // 3. Filtro y orden solo cuentan la valoración verificada.
  {
    const { context, page } = await open(market);
    assert.equal(await page.locator('[data-filter="valoracion"]').isEnabled(), true);
    await page.locator('[data-filter="valoracion"]').evaluate(e => { const d = e.closest('details'); if (d) d.open = true; });
    await page.selectOption('[data-filter="valoracion"]', { index: 1 });
    const shown = await page.locator('.catalogue-card:not([hidden])').evaluateAll(cards => cards.map(c => c.dataset.bookId));
    assert.deepEqual(shown, [verified], 'el filtro de valoración solo deja la valoración verificada');
    await page.selectOption('[data-filter="valoracion"]', '');
    await page.selectOption('[data-filter="orden"]', 'valoracion_desc');
    const first = await page.locator('.catalogue-card:not([hidden])').first().getAttribute('data-book-id');
    assert.equal(first, verified, 'ordenar por valoración pone primero la verificada, no las muestras pequeñas');
    await context.close();
  }

  // 4. Sin JS no hay notas fabricadas.
  {
    const { context, page } = await open(market, { javaScriptEnabled: false });
    for (const b of await boxes(page)) unverifiedOk(b, 'sin JS');
    await context.close();
  }
} finally {
  await browser.close();
}
console.log('PASS catalogue ratings trust: verified, small sample, expired, forged source, no data, provider failure');
