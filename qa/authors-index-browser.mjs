import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = process.env.RECOMMENDATIONS_BASE_URL || process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {});
const errors = [];
try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  page.on('pageerror', error => errors.push(String(error)));
  await page.goto(`${base}/recomendaciones/autores/`, { waitUntil: 'load' });
  await page.waitForFunction(() => document.querySelectorAll('[data-index-list] > li').length === 24);

  const total = await page.locator('[data-index-count]').evaluate(el => Number(el.textContent.match(/\d+/)?.[0]));
  assert.ok(total >= 500, `El índice conserva el conjunto completo de autores (${total})`);
  assert.equal(await page.locator('[data-index-list] > li').count(), 24, 'Paginación inicial limita las tarjetas renderizadas');
  assert.ok(await page.locator('.catalogue-sidebar').evaluate(side => side.getBoundingClientRect().right <= document.querySelector('.catalogue-main').getBoundingClientRect().left + 1), 'Los filtros quedan a la izquierda en escritorio');

  const cards = page.locator('[data-index-list] > li');
  assert.match(await page.locator('.catalogue-author-card__profile').first().getAttribute('aria-label'), /^Ver ficha de /, 'La portada enlazada a la ficha tiene nombre accesible');
  const affiliate = page.locator('.catalogue-author-card .catalogue-card__buy').first();
  const affiliateUrl = new URL(await affiliate.getAttribute('href'));
  assert.equal(affiliateUrl.hostname, 'www.amazon.es');
  assert.equal(affiliateUrl.searchParams.get('tag'), 'davidporto-21');
  assert.equal(await affiliate.getAttribute('rel'), 'sponsored nofollow noopener noreferrer');

  const facets = await page.locator('[data-index-filter="tipo"]').evaluateAll(fields => fields.map(field => ({ value: field.value, count: Number(field.parentElement.querySelector('small').textContent) })));
  assert.ok(facets.length > 1 && facets.every(facet => facet.count > 0), 'Cada tipo de libro ofrece un recuento no vacío');
  const checkbox = value => page.locator(`[data-index-filter="tipo"][value="${value}"]`);
  const filterMs = await page.evaluate(value => {
    const field = document.querySelector(`[data-index-filter="tipo"][value="${value}"]`);
    const start = performance.now();
    field.checked = true;
    field.dispatchEvent(new Event('change', { bubbles: true }));
    return performance.now() - start;
  }, facets[0].value);
  assert.ok(filterMs < 250, `Filtrar ${total} autores tarda menos de 250 ms (${filterMs.toFixed(1)} ms)`);
  await checkbox(facets[0].value).uncheck();
  for (const facet of facets) {
    await checkbox(facet.value).check();
    const visibleGroups = await cards.evaluateAll(elements => elements.map(card => card.dataset.groups.split(' ')));
    assert.ok(visibleGroups.length > 0 && visibleGroups.every(groups => groups.includes(facet.value)), `El filtro ${facet.value} limita resultados correctamente`);
    assert.match(await page.evaluate(() => location.hash), new RegExp(`tipo=${facet.value}`));
    await checkbox(facet.value).uncheck();
  }

  await checkbox(facets[0].value).check();
  await checkbox(facets[1].value).check();
  const combinedGroups = await cards.evaluateAll(elements => elements.map(card => card.dataset.groups.split(' ')));
  assert.ok(combinedGroups.length > 0 && combinedGroups.every(groups => groups.includes(facets[0].value) || groups.includes(facets[1].value)), 'Varios tipos se combinan con lógica O');
  assert.equal(new URLSearchParams(new URL(page.url()).hash.slice(1)).getAll('tipo').length, 2, 'La URL conserva las facetas múltiples');
  await page.locator('[type="reset"]').click();

  const name = await page.locator('[data-index-list] h3').first().textContent();
  const searchField = page.locator('[data-index-filter="q"]');
  await searchField.fill(name.trim());
  await page.waitForFunction(() => new URLSearchParams(location.hash.slice(1)).has('q'));
  assert.ok((await cards.count()) <= 24 && (await cards.first().textContent()).toLowerCase().includes(name.trim().toLowerCase()), 'La búsqueda por nombre devuelve el autor esperado');
  await page.locator('[type="reset"]').click();

  const bookSummary = await page.locator('.catalogue-author-card__books').first().textContent();
  const title = bookSummary.split(' · ').slice(1).join(' · ').replace(/…$/, '').split(', ')[0].trim();
  await searchField.fill(title);
  await page.waitForFunction(() => new URLSearchParams(location.hash.slice(1)).has('q'));
  assert.ok(await cards.first().evaluate((card, bookTitle) => card.dataset.search.toLowerCase().includes(bookTitle.toLowerCase()), title), 'La búsqueda también encuentra títulos de libros');
  await searchField.fill('sin-resultados-para-este-texto');
  await page.waitForFunction(() => document.querySelector('[data-index-count]').textContent.includes('Mostrando 0 de'));
  assert.equal(await page.locator('[data-index-empty]').isVisible(), true, 'La búsqueda vacía explica que no hay resultados');
  await page.locator('[type="reset"]').click();

  const stateField = page.locator('[data-index-filter="estado"]');
  const indexDate = await page.locator('.catalogue-authors-index').getAttribute('data-index-date');
  await stateField.selectOption('proximos');
  let dateSets = await cards.evaluateAll(elements => elements.map(card => (card.dataset.dates || '').split(' ').filter(Boolean)));
  assert.ok(dateSets.length > 0 && dateSets.every(dates => dates.some(date => date > indexDate)), 'Próximos lanzamientos usan la fecha de referencia del catálogo');
  await stateField.selectOption('novedad');
  const cutoff = new Date(indexDate + 'T00:00:00Z');
  cutoff.setUTCDate(cutoff.getUTCDate() - 30);
  const minimumDate = cutoff.toISOString().slice(0, 10);
  dateSets = await cards.evaluateAll(elements => elements.map(card => (card.dataset.dates || '').split(' ').filter(Boolean)));
  assert.ok(dateSets.length > 0 && dateSets.every(dates => dates.some(date => date <= indexDate && date >= minimumDate)), 'Novedades recientes usan la misma fecha de referencia');
  await page.locator('[type="reset"]').click();

  await page.locator('[data-index-filter="orden"]').selectOption('libros');
  let bookCounts = await cards.evaluateAll(elements => elements.map(card => Number(card.dataset.books)));
  assert.deepEqual(bookCounts, [...bookCounts].sort((a, b) => b - a), 'La ordenación por número de libros es descendente');
  await page.locator('[type="reset"]').click();

  await page.locator('[data-index-pagination] button[aria-label="Autores siguientes"]').click();
  assert.match(new URL(page.url()).hash, /pagina=2/);
  assert.equal(await page.locator('[data-index-list] > li').count(), 24, 'La página siguiente muestra un nuevo conjunto limitado');
  assert.match(await page.locator('[data-index-pagination]').textContent(), /Página 2 de/);
  assert.equal(await page.evaluate(() => document.activeElement.id), 'authors-list', 'La paginación devuelve el foco al encabezado de resultados');
  await page.goto(`${base}/recomendaciones/autores/#pagina=2`, { waitUntil: 'load' });
  await page.waitForFunction(() => document.querySelector('[data-index-pagination]')?.textContent.includes('Página 2 de'));

  const quiz = page.locator('.catalogue-authors-quiz');
  await quiz.locator('summary').click();
  await quiz.locator('[data-author-quiz-type]').selectOption(facets[0].value);
  await quiz.locator('[data-author-quiz-submit]').click();
  assert.ok(await page.locator('[data-index-filter="tipo"]:checked').count() === 1, 'El test aplica el tipo elegido a los filtros');
  assert.ok((await cards.evaluateAll((elements, kind) => elements.every(card => card.dataset.groups.split(' ').includes(kind)), facets[0].value)), 'El test solo recomienda autores del tipo elegido');

  const mobile = await browser.newPage({ viewport: { width: 390, height: 844 } });
  mobile.on('pageerror', error => errors.push(String(error)));
  await mobile.goto(`${base}/recomendaciones/autores/`, { waitUntil: 'load' });
  await mobile.waitForFunction(() => document.querySelectorAll('[data-index-list] > li').length === 24);
  const toggle = mobile.locator('[data-author-filter-toggle]');
  assert.equal(await toggle.getAttribute('aria-expanded'), 'false', 'Los filtros móviles comienzan plegados');
  assert.equal(await mobile.locator('#authors-filter-panel').isVisible(), false);
  await toggle.click();
  assert.equal(await mobile.locator('#authors-filter-panel').isVisible(), true, 'El botón despliega los filtros móviles');
  assert.ok(await mobile.locator('[data-index-list]').evaluate(list => list.getBoundingClientRect().right <= document.documentElement.clientWidth), 'Las tarjetas no desbordan el viewport móvil');
  await mobile.close();

  const noJs = await browser.newPage();
  await noJs.route('**/assets/catalogue-authors.js*', route => route.abort());
  await noJs.goto(`${base}/recomendaciones/autores/`, { waitUntil: 'load' });
  assert.equal(await noJs.locator('[data-index-list] > li').count(), total, 'Sin JavaScript quedan todos los autores accesibles');
  assert.equal(await noJs.locator('[data-index-filter="q"]').isDisabled(), true, 'Sin JavaScript no hay controles de búsqueda inertes');
  assert.equal(await noJs.locator('[data-author-filter-toggle]').isDisabled(), true, 'Sin JavaScript no hay controles de filtros inertes');
  await noJs.close();

  const publishers = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  publishers.on('pageerror', error => errors.push(String(error)));
  await publishers.goto(`${base}/recomendaciones/editoriales/`, { waitUntil: 'load' });
  await publishers.waitForFunction(() => document.querySelector('select[data-index-filter="tipo"]')?.disabled === false);
  const publisherType = publishers.locator('select[data-index-filter="tipo"]');
  const publisherKind = await publisherType.locator('option').evaluateAll(options => options.find(option => option.value)?.value);
  await publisherType.selectOption(publisherKind);
  const publisherCards = publishers.locator('[data-index-list] > li');
  assert.ok(await publisherCards.count() > 0);
  assert.match(await publishers.locator('[data-index-count]').textContent(), /sellos$/, 'El contador conserva el sustantivo del índice de editoriales');
  assert.ok((await publisherCards.evaluateAll((elements, kind) => elements.every(card => card.dataset.groups.split(' ').includes(kind)), publisherKind)), 'Los filtros de tipos siguen funcionando en el índice de editoriales');
  const ownerSelect = publishers.locator('select[data-index-filter="grupo"]');
  if (await ownerSelect.count()) {
    const owner = await ownerSelect.locator('option').evaluateAll(options => options.find(option => option.value)?.value);
    await ownerSelect.selectOption(owner);
    assert.ok((await publisherCards.evaluateAll((elements, selectedOwner) => elements.every(card => card.dataset.owner === selectedOwner), owner)), 'Los filtros de grupos siguen funcionando en el índice de editoriales');
  }
  await publishers.close();

  assert.deepEqual(errors, [], 'La página no produce errores JavaScript');
  console.log(`Authors/publishers index browser QA passed (${total} authors, ${facets.length} book types, desktop/mobile/no-JS).`);
} finally {
  await browser.close();
}
