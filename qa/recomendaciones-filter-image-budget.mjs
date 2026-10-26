import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  const images = [];
  page.on('request', request => {
    if (request.resourceType() === 'image' && request.url().includes('/assets/reading-covers/')) images.push(request.url());
  });
  const response = await page.goto(`${ORIGIN}/recomendaciones/`, { waitUntil: 'domcontentloaded' });
  assert.equal(response?.ok(), true, '/recomendaciones/: fallo de carga');
  const cards = page.locator('[data-catalogue-book]');
  const total = await cards.count();
  assert.ok(total > 20, `/recomendaciones/: catálogo inesperadamente pequeño: ${total}`);
  const first = cards.first();
  const isbn = (await first.getAttribute('data-search'))?.match(/\b\d{13}\b/)?.[0];
  assert.ok(isbn, '/recomendaciones/: primera ficha sin ISBN buscable');
  const search = page.locator('[data-catalogue-filters] [data-filter="q"]');
  await search.waitFor({ state: 'visible' });
  await page.waitForFunction(() => !document.querySelector('[data-catalogue-filters] fieldset')?.disabled);
  await search.fill(isbn);
  await page.waitForFunction(value => {
    const cards = [...document.querySelectorAll('[data-catalogue-book]')];
    return cards.some(card => !card.hidden && card.dataset.search.includes(value)) && cards.filter(card => !card.hidden).length < cards.length;
  }, isbn);
  const visible = await page.locator('[data-catalogue-book]:visible').count();
  assert.ok(visible > 0 && visible < total, `/recomendaciones/: filtro ISBN ${isbn} no reduce resultados`);
  const distinct = new Set(images);
  assert.ok(distinct.size < total, `/recomendaciones/: ${distinct.size} portadas solicitadas para ${total} libros; revisar carga diferida`);
  console.log('recomendaciones-filter-image-budget: PASS');
} finally {
  await browser.close();
}