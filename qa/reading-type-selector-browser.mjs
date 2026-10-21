// Selector «Tipo de libro» junto al catálogo y orden por defecto por fecha de publicación.
import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = process.env.RECOMMENDATIONS_BASE_URL || process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {});
try {
  for (const viewport of [{ width: 1280, height: 900 }, { width: 390, height: 844 }]) {
    const page = await browser.newPage({ viewport });
    const errors = [];
    page.on('pageerror', error => errors.push(String(error)));
    await page.addInitScript(() => sessionStorage.setItem('dp-intro-seen', '1'));
    await page.goto(`${base}/recomendaciones/`, { waitUntil: 'load' });
    await page.locator('[data-type-radio]').first().waitFor();
    await page.waitForFunction(() => !document.querySelector('[data-type-radio]').disabled);
    const total = await page.locator('[data-catalogue-book]').count();
    const radios = await page.locator('[data-type-radio]').evaluateAll(list => list.map(r => ({ value: r.value, checked: r.checked })));
    assert.equal(radios[0].value, '', 'La primera opción es «Todos»');
    assert.equal(radios[0].checked, true, '«Todos» marcado por defecto');
    assert.equal(radios[1].value, 'novela', '«Novela» es la primera categoría');
    const counts = await page.locator('[data-type-radio]').evaluateAll(list => list.map(r => Number(r.parentElement.querySelector('small').textContent.replace(/\D/g, ''))));
    assert.equal(counts[0], total, 'El total de «Todos» coincide con las fichas');
    assert.equal(counts.slice(1).reduce((a, b) => a + b, 0), total, 'Cada libro pertenece a un único tipo');

    const dates = await page.locator('[data-catalogue-book]').evaluateAll(cards => cards.map(c => c.dataset.published || (c.dataset.publishedMonth ? c.dataset.publishedMonth + '-01' : c.dataset.year ? c.dataset.year + '-01-01' : '')));
    const dated = dates.filter(Boolean);
    assert.deepEqual(dated, [...dated].sort().reverse(), 'Orden por defecto: publicación más reciente primero');

    for (const option of radios.slice(1)) {
      await page.locator(`[data-type-radio][value="${option.value}"]`).check();
      const visible = await page.locator('[data-catalogue-book]:not([hidden])').evaluateAll(cards => cards.map(c => c.dataset.group));
      assert.ok(visible.length > 0 && visible.every(group => group === option.value), `Filtrar por ${option.value} solo muestra ese tipo`);
      assert.match(await page.evaluate(() => location.hash), new RegExp(`grupo=${option.value}`));
    }
    await page.locator('[type="reset"]').first().click();
    await page.waitForFunction(total => document.querySelectorAll('[data-catalogue-book]:not([hidden])').length > 0 && document.querySelector('[data-type-radio][value=""]').checked, total);
    await page.goto(`${base}/recomendaciones/#grupo=cocina`, { waitUntil: 'load' });
    await page.waitForFunction(() => document.querySelector('[data-type-radio][value="cocina"]')?.checked);
    await page.waitForFunction(() => [...document.querySelectorAll('[data-rating-book]')].every(box => box.textContent.trim()));
    const unrated = await page.locator('[data-rating-book]:not(:has(.catalogue-stars)) a').allInnerTexts();
    assert.ok(unrated.every(text => text.startsWith('Aún sin valoraciones públicas')), 'Sin valoración verificada se indica con honestidad');
    assert.equal(await page.locator('.catalogue-extra-tags').count(), 0, 'Sin desplegable de «Más categorías» en las tarjetas');
    assert.deepEqual(errors, [], 'Sin errores de JavaScript');
    await page.close();
  }
  console.log('PASS selector de tipo de libro y orden por fecha (escritorio y móvil).');
} finally {
  await browser.close();
}
