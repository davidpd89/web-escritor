import assert from 'node:assert/strict';
import { chromium } from 'playwright';

assert.ok(process.env.SITE_ORIGIN, 'SITE_ORIGIN es obligatorio');
const origin = new URL(process.env.SITE_ORIGIN).origin;
const browser = await chromium.launch({
  headless: true,
  ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {})
});

try {
  const context = await browser.newContext({ viewport: { width: 390, height: 900 } });
  // El test solo permite solicitudes al servidor local del repositorio.
  await context.route('**/*', route => {
    const requested = new URL(route.request().url());
    return requested.origin === origin ? route.continue() : route.abort();
  });

  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(`${origin}/recomendaciones/`);
  await page.waitForFunction(() => {
    const fieldset = document.querySelector('[data-catalogue-filters] fieldset');
    return fieldset && !fieldset.disabled;
  });

  const query = page.locator('[data-filter="q"]');
  const ids = () => page.locator('[data-catalogue-book]:visible').evaluateAll(cards =>
    cards.map(card => card.dataset.bookId).sort()
  );
  const search = async value => {
    await query.fill(value);
    return ids();
  };

  // Criterio principal: cuatro representaciones del mismo ISBN dan las mismas fichas.
  const canonical = await search('9791388092268');
  assert(canonical.length > 0, 'El ISBN canónico debe devolver resultados');
  assert(canonical.includes('isbn-9791388092268'), 'Debe aparecer Ponte fino');

  for (const value of [
    '979-13-8809-226-8',
    '979 13 8809 226 8',
    'ISBN 979-13-8809-226-8',
    'ISBN-13: 979-13-8809-226-8',
    'ISBN: 9791388092268',
    'isbn-13 979 13 8809 226 8'
  ]) {
    assert.deepEqual(await search(value), canonical, `El ISBN ${value} no devuelve las mismas fichas`);
  }

  // Los ISBN-13 inexistentes siguen devolviendo cero fichas.
  for (const value of ['9790000000000', 'ISBN-13: 979-00-0000-000-0']) {
    assert.deepEqual(await search(value), [], `El ISBN inexistente ${value} no debe coincidir`);
    assert(await page.locator('[data-catalogue-empty]').isVisible());
  }

  // Se guarda la entrada original, no la versión sin separadores.
  const persisted = 'ISBN 979-13-8809-226-8';
  assert.deepEqual(await search(persisted), canonical);
  assert.equal(new URLSearchParams(new URL(page.url()).hash.slice(1)).get('q'), persisted);
  await page.reload();
  assert.equal(await query.inputValue(), persisted);
  assert.deepEqual(await ids(), canonical);

  // Una búsqueda numérica ordinaria no se interpreta como ISBN.
  const nineteenEightyFour = await search('1984');
  assert(nineteenEightyFour.includes('isbn-9788491058298'), '1984 debe seguir encontrando su libro');

  // La normalización de tildes y mayúsculas debe permanecer intacta.
  const accented = await search('La hipótesis más peligrosa');
  assert(accented.includes('isbn-9791387846008'));
  assert.deepEqual(await search('la hipotesis mas peligrosa'), accented);

  // Los autores se siguen buscando mediante la normalización habitual.
  const author = await search('Martín Berasategui');
  assert(author.includes('isbn-9791388092268'));
  assert.deepEqual(await search('martin berasategui'), author);

  assert.deepEqual(errors, [], 'No debe haber errores JavaScript en el catálogo');
  await context.close();
  console.log('PASS MW-0027: ISBN-13 equivalentes, inexistentes, persistencia y búsquedas ordinarias');
} finally {
  await browser.close();
}
