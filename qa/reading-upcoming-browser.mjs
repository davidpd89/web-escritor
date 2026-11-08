// «Ver los próximos lanzamientos» (bug de David, 07/11: «va fatal y no pagina»). Con el catálogo real generado:
// el enlace lleva a los próximos en menos de un límite, ordenados del más cercano al más lejano, sin libros ya
// publicados, y la paginación avanza, retrocede y sobrevive a recargar la página.
import {chromium} from 'playwright';
import assert from 'node:assert/strict';

const base = process.env.RECOMMENDATIONS_BASE_URL || 'http://127.0.0.1:4173';
const limitMs = Number(process.env.UPCOMING_LIMIT_MS || 8000);
const browser = await chromium.launch({headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});
const results = [];
const today = new Date().toISOString().slice(0, 10);

async function visible(page) {
  return page.$$eval('.catalogue-grid > [data-catalogue-book]:not([hidden])', cards => cards.map(card => ({
    id: card.dataset.bookId, published: card.dataset.published || card.dataset.publishedMonth || card.dataset.year || ''})));
}

const countText = page => page.locator('[data-catalogue-count]').innerText();

try {
  for (const viewport of [{width: 1280, height: 900}, {width: 390, height: 844}]) {
    const context = await browser.newContext({viewport, reducedMotion: 'reduce'});
    await context.addInitScript(() => localStorage.setItem('nl-popup-ts', String(Date.now())));
    const page = await context.newPage(), errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto(base + '/recomendaciones/', {waitUntil: 'domcontentloaded'});
    const link = page.locator('[data-catalogue-upcoming]');
    await link.waitFor({state: 'visible'});
    const started = Date.now();
    await link.click();
    await page.waitForFunction(() => /página 1 de \d+/.test(document.querySelector('[data-catalogue-count]')?.textContent || ''), null, {timeout: 60000});
    const elapsed = Date.now() - started;
    const first = await visible(page);
    const label = await countText(page);
    const total = Number(label.match(/^(\d+)/)[1]), pages = Number(label.match(/de (\d+)/)[1]);
    assert.ok(total > 24, `hay más de una página de próximos: ${label}`);
    assert.equal(first.length, 24, 'la primera página trae 24 libros');
    assert.ok(first.every(b => b.published >= today.slice(0, b.published.length)), 'ningún libro ya publicado: ' + JSON.stringify(first.filter(b => b.published < today).slice(0, 3)));
    const dates = first.map(b => b.published);
    assert.deepEqual(dates, [...dates].sort(), 'del más cercano al más lejano');
    assert.match(page.url(), /estado=proximos/);
    // Avanzar: otra página, más lejana y con la URL al día.
    const next = page.locator('[data-catalogue-pagination] button', {hasText: /Siguiente/});
    await next.click();
    await page.waitForFunction(() => /página 2 de/.test(document.querySelector('[data-catalogue-count]')?.textContent || ''));
    const second = await visible(page);
    assert.equal(second.length, 24);
    assert.ok(second.every(b => !first.some(f => f.id === b.id)), 'la página 2 no repite libros');
    assert.ok(second[0].published >= first.at(-1).published, 'la página 2 sigue después de la 1');
    assert.match(page.url(), /pagina=2/);
    // Recargar conserva página y estado.
    await page.reload({waitUntil: 'domcontentloaded'});
    await page.waitForFunction(() => /página 2 de/.test(document.querySelector('[data-catalogue-count]')?.textContent || ''), null, {timeout: 60000});
    assert.deepEqual((await visible(page)).map(b => b.id), second.map(b => b.id), 'recargar enseña la misma página 2');
    // Última página: el resto, sin huecos.
    const last = page.locator(`[data-catalogue-pagination] button[aria-label="Página ${pages}"]`);
    if (await last.count()) {
      await last.click();
      await page.waitForFunction(p => document.querySelector('[data-catalogue-count]')?.textContent.includes(`página ${p} de`), pages);
      assert.equal((await visible(page)).length, total - 24 * (pages - 1));
    }
    assert.deepEqual(errors, []);
    results.push({viewport: viewport.width, ms: elapsed, total, pages});
    assert.ok(elapsed < limitMs, `«Ver los próximos lanzamientos» tarda ${elapsed} ms (límite ${limitMs})`);
    await context.close();
  }
  console.log('PASS próximos lanzamientos', JSON.stringify(results));
} finally {
  await browser.close();
}
