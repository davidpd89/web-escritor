import assert from 'node:assert/strict';
import { chromium } from 'playwright';

// Valoraciones (David, 2026-11-08): la Creators API no las da, así que no se pinta ninguna nota en ningún
// sitio. Fuera de la ficha no hay nada (ni caja, ni estrellas, ni filtro, ni orden); la ficha solo enlaza a
// Goodreads por ISBN, aunque reading-market.json traiga una nota «verificada». Antes (#1005) 62 de 88
// tarjetas mostraban «Goodreads ★★★★★ 0,0 (0)».
const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const now = Date.parse('2026-10-30T12:00:00Z');
const iso = ms => new Date(ms).toISOString().replace('.000Z', 'Z');
const dated = { actualizado_en: iso(now - 3600000), caduca_en: iso(now + 72 * 3600000) };
const stale = { actualizado_en: iso(now - 200 * 3600000), caduca_en: iso(now - 32 * 3600000) };
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

async function open(market, { width = 1280, javaScriptEnabled = true, path = '/recomendaciones/#orden=titulo' } = {}) {
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
  await page.goto(origin + path, { waitUntil: 'networkidle' });
  return { context, page, external };
}
const noScores = async (page, where) => {
  assert.equal(await page.locator('.catalogue-stars').count(), 0, `${where}: estrellas`);
  assert.doesNotMatch(await page.locator('main').innerText(), /★|\d,\d \(\d/, `${where}: una nota a la vista`);
};
const cards = page => page.locator('.catalogue-card:not([hidden])').evaluateAll(list => list.map(c => ({ id: c.dataset.bookId, href: c.querySelector('.catalogue-card__ficha')?.getAttribute('href') })));

try {
  const visible = await (async () => { const { context, page } = await open({ schema_version: 1, offers: [], ratings: [] }); const all = await cards(page); await context.close(); return all; })();
  assert.ok(visible.length > 20, 'el catálogo debe tener tarjetas');
  const ids = visible.slice(0, 6).map(c => c.id);
  const market = { schema_version: 1, offers: [], ratings: [
    { ...dated, libro_id: ids[0], fuente: 'goodreads', puntuacion: 4.2, numero_valoraciones: 12345, url: 'https://www.goodreads.com/book/show/101' },
    { ...dated, libro_id: ids[1], fuente: 'amazon', puntuacion: 4.6, numero_valoraciones: 900, url: 'https://www.amazon.es/dp/B000000001' },
    { ...dated, libro_id: ids[2], fuente: 'hardcover', puntuacion: 1, numero_valoraciones: 1, url: 'https://hardcover.app/books/qa-uno' },
  ] };

  // 1. Listado: con proveedor caído, sin datos o con notas en el mercado, ninguna valoración, filtro ni orden.
  for (const [where, m] of [['proveedor caído', 'fail'], ['sin dato', { schema_version: 1, offers: [], ratings: [] }], ['con notas', market]]) {
    for (const width of where === 'con notas' ? [390, 768, 1280] : [1280]) {
      const { context, page, external } = await open(m, { width });
      assert.equal(await page.locator('[data-rating-book]').count(), 0, `${where}: caja de valoración en el listado`);
      assert.equal(await page.locator('[data-filter="valoracion"], option[value="valoracion_desc"]').count(), 0, `${where}: filtro u orden por valoración`);
      await noScores(page, `${where} @${width}`);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      assert.ok(overflow <= 0, `${width}px: scroll horizontal de ${overflow} px`);
      assert.deepEqual(external, [], 'no se piden recursos externos');
      await context.close();
    }
  }

  // 2. Ficha: solo el enlace a Goodreads por ISBN, aunque el mercado traiga una nota.
  {
    const href = visible.find(c => c.id === ids[0])?.href;
    assert.ok(href, 'la tarjeta enlaza a su ficha');
    for (const m of [market, 'fail']) {
      const { context, page } = await open(m, { path: new URL(href, origin).pathname });
      const box = page.locator('[data-rating-book]');
      assert.equal(await box.count(), 1);
      const isbn = await box.getAttribute('data-isbn');
      if (/^\d{13}$/.test(isbn || '')) {
        const link = box.locator('a');
        await link.waitFor();
        assert.equal(await link.innerText(), 'Goodreads · ver opiniones');
        assert.equal(await link.getAttribute('href'), `https://www.goodreads.com/book/isbn/${isbn}`);
      } else assert.equal(await box.isHidden(), true, 'sin ISBN no hay enlace que ofrecer');
      await noScores(page, 'ficha');
      await context.close();
    }
  }

  // 3. Más vendidos: solo se ofrece con puestos vigentes de Amazon.es; con puesto primero (1, 2…), el resto después.
  {
    const option = page => page.locator('[data-filter="orden"] option[value="ventas"]');
    const empty = await open({ schema_version: 1, offers: [], ratings: [] });
    assert.equal(await option(empty.page).evaluate(o => o.disabled && o.hidden), true, 'sin puestos no se ofrece «más vendidos»');
    await empty.context.close();
    const [top, second, old] = ids.slice(3, 6);
    const ranks = { schema_version: 1, offers: [], ratings: [], sales_ranks: [
      { ...dated, libro_id: second, posicion: 40, fuente: 'amazon_es_books' },
      { ...dated, libro_id: top, posicion: 7, fuente: 'amazon_es_books' },
      { ...stale, libro_id: old, posicion: 1, fuente: 'amazon_es_books' },
      { ...dated, libro_id: ids[0], posicion: 2, fuente: 'otra_tienda' },
    ] };
    const { context, page } = await open(ranks);
    assert.equal(await option(page).evaluate(o => !o.disabled && !o.hidden), true, 'con puestos vigentes se ofrece «más vendidos»');
    await page.selectOption('[data-filter="orden"]', 'ventas');
    const order = await page.locator('.catalogue-card:not([hidden])').evaluateAll(list => list.slice(0, 2).map(c => c.dataset.bookId));
    assert.deepEqual(order, [top, second], 'los más vendidos van primero, del menor puesto al mayor; caducados y otras fuentes no cuentan');
    await context.close();
  }

  // 4. Sin JS tampoco hay notas.
  {
    const { context, page } = await open(market, { javaScriptEnabled: false });
    await noScores(page, 'sin JS');
    await context.close();
  }
} finally {
  await browser.close();
}
console.log('PASS catalogue ratings: no scores anywhere; the book page only links to Goodreads by ISBN');
