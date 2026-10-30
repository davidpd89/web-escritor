// Filtros con casillas junto al catálogo: tipo de libro, varias opciones a la vez y recuentos dependientes.
import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = process.env.RECOMMENDATIONS_BASE_URL || process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
// En móvil (≤900 px) los filtros se pliegan tras «Filtros» (#1004): abrirlos como haría el lector.
const openFilters = async page => { const toggle = page.locator('[data-catalogue-refine-toggle]'); if (await toggle.isVisible() && await toggle.getAttribute('aria-expanded') === 'false') await toggle.click(); };
const browser = await chromium.launch(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {});
try {
  for (const viewport of [{ width: 1280, height: 900 }, { width: 390, height: 844 }]) {
    const page = await browser.newPage({ viewport });
    const errors = [];
    page.on('pageerror', error => errors.push(String(error)));
    await page.addInitScript(() => sessionStorage.setItem('dp-intro-seen', '1'));
    await page.goto(`${base}/recomendaciones/`, { waitUntil: 'load' });
    await openFilters(page);
    const box = (facet, value) => page.locator(`input[data-facet="${facet}"][value="${value}"]`);
    const visibleBooks = () => page.locator('[data-catalogue-book]:not([hidden])');
    await page.locator('input[data-facet="grupo"]').first().waitFor({ state: 'attached' });
    await page.waitForFunction(() => !document.querySelector('input[data-facet="grupo"]').disabled || document.querySelector('[data-facet-count]').textContent.includes('('));
    const total = await page.locator('[data-catalogue-book]').count();
    const types = await page.locator('input[data-facet="grupo"]').evaluateAll(list => list.map(r => ({ value: r.value, count: Number(r.parentElement.querySelector('small').textContent.replace(/\D/g, '')), checked: r.checked })));
    assert.ok(types.length >= 2 && types.every(t => !t.checked), 'Ningún tipo marcado: se ven todos los libros');
    assert.equal(types[0].value, 'novela', '«Novela» es la primera categoría');
    assert.equal(types.reduce((sum, t) => sum + t.count, 0), total, 'Cada libro pertenece a un único tipo');
    // Las casillas viven junto al catálogo (columna lateral), no encima.
    const layout = await page.evaluate(() => { const side = document.querySelector('.catalogue-sidebar').getBoundingClientRect(), grid = document.querySelector('.catalogue-grid').getBoundingClientRect(); return { sideRight: side.right, gridLeft: grid.left, sideBottom: side.bottom, gridTop: grid.top }; });
    if (viewport.width > 900) assert.ok(layout.sideRight <= layout.gridLeft + 1, 'En escritorio los filtros quedan al lado del catálogo');

    const dates = await page.locator('[data-catalogue-book]').evaluateAll(cards => cards.map(c => c.dataset.published || (c.dataset.publishedMonth ? c.dataset.publishedMonth + '-01' : c.dataset.year ? c.dataset.year + '-01-01' : '')));
    const dated = dates.filter(Boolean);
    assert.deepEqual(dated, [...dated].sort().reverse(), 'Orden por defecto: publicación más reciente primero');

    for (const option of types.filter(t => t.count > 0)) {
      await page.locator(`details[data-facet-group="grupo"]`).evaluate(el => { el.open = true; });
      await box('grupo', option.value).check();
      const groups = await visibleBooks().evaluateAll(cards => cards.map(c => c.dataset.group));
      assert.ok(groups.length > 0 && groups.every(group => group === option.value), `Filtrar por ${option.value} solo muestra ese tipo`);
      assert.match(await page.evaluate(() => location.hash), new RegExp(`grupo=${option.value}`));
      await box('grupo', option.value).uncheck();
    }

    // Varias opciones dentro de un mismo filtro suman (O); cruzar filtros distintos restringe (Y).
    await page.locator('details[data-facet-group="genero"]').evaluate(el => { el.open = true; });
    await box('genero', 'fantasia').check();
    const fantasy = await visibleBooks().count();
    await box('genero', 'terror').check();
    const either = await visibleBooks().count();
    assert.ok(either >= fantasy, 'Fantasía O Terror muestra al menos los de Fantasía');
    const eitherIds = await visibleBooks().evaluateAll(cards => cards.map(c => c.dataset.categories.split(' ').some(x => x === 'fantasia' || x === 'terror')));
    assert.ok(eitherIds.every(Boolean), 'Cada libro visible tiene Fantasía o Terror');
    assert.match(await page.evaluate(() => location.hash), /genero=fantasia.*genero=terror|genero=terror.*genero=fantasia/);
    await page.goto(`${base}/recomendaciones/#genero=fantasia&genero=terror`, { waitUntil: 'load' });
    await page.waitForFunction(() => document.querySelector('input[data-facet="genero"][value="terror"]')?.checked);
    assert.equal(await visibleBooks().count(), Math.min(either, 24), 'Recuperar la URL restaura la selección múltiple');
    await page.waitForFunction(() => [...document.querySelectorAll('[data-rating-book]')].every(box => box.textContent.trim()));
    const ratings = await page.locator('[data-rating-book] a').allInnerTexts();
    assert.ok(ratings.length > 0 && ratings.every(text => /^(Goodreads|Hardcover|Google Books)/.test(text) && (/\d,\d+\s+\(\d/.test(text) || /· (consultar ficha|menos de 5 valoraciones)$/.test(text)) && !/0,0 \(0\)/.test(text)), 'Valoración: fuente y nota (n) verificada, o enlace neutro; nunca 0,0 (0)');
    const tagCounts = await page.locator('[data-catalogue-book] .catalogue-tags li').evaluateAll(list => list.length);
    assert.ok(await page.locator('[data-catalogue-book]').evaluateAll(cards => cards.every(c => c.querySelectorAll('.catalogue-tags li').length <= 3)), 'Máximo 3 categorías por tarjeta');
    assert.ok(tagCounts >= 0);
    assert.equal(await page.locator('.catalogue-extra-tags').count(), 0, 'Sin desplegable de «Más categorías» en las tarjetas');

    // Filtros dependientes: con un tipo elegido, las opciones sin libros compatibles quedan desactivadas y vuelven al quitarlo.
    await page.locator('[type="reset"]').first().click();
    await page.waitForFunction(() => document.querySelectorAll('input[data-facet]:checked').length === 0);
    await page.locator('details[data-facet-group="grupo"]').evaluate(el => { el.open = true; });
    await box('grupo', 'cocina').check();
    const disabledNow = await page.locator('input[data-facet="genero"]:disabled').evaluateAll(list => list.map(o => o.value));
    assert.ok(disabledNow.length > 0, 'Con «Cocina» hay géneros sin libros desactivados');
    for (const value of disabledNow.slice(0, 5)) {
      assert.equal(await page.locator(`[data-catalogue-book][data-group="cocina"][data-categories~="${value}"]`).count(), 0, `La opción desactivada ${value} no tiene libros de cocina`);
    }
    await box('grupo', 'cocina').uncheck();
    const stillDisabled = await page.locator('input[data-facet="genero"]:disabled').evaluateAll(list => list.map(o => o.value));
    for (const value of stillDisabled) assert.equal(await page.locator(`[data-catalogue-book][data-categories~="${value}"]`).count(), 0, `Sin tipo elegido solo queda desactivado lo que no tiene ningún libro (${value})`);
    assert.ok(stillDisabled.length < disabledNow.length, 'Quitar el tipo vuelve a activar opciones');
    assert.deepEqual(errors, [], 'Sin errores de JavaScript');
    await page.close();
  }
  console.log('PASS filtros con casillas, tipo de libro y orden por fecha (escritorio y móvil).');
} finally {
  await browser.close();
}
