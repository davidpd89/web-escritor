import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = process.env.BASE_URL || process.env.SITE_URL || 'http://127.0.0.1:8000';
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext();
try {
  const page = await context.newPage();
  await page.goto(new URL('/recomendaciones/', base).href);
  const root = page.locator('[data-reading-catalogue]');
  const search = root.locator('[data-filter="q"]');
  await assert.doesNotReject(() => search.waitFor({ state: 'visible' }));
  await assert.doesNotReject(() => page.waitForFunction(() => !document.querySelector('[data-catalogue-filters] fieldset')?.disabled));
  const first = root.locator('[data-catalogue-book]').first();
  const title = await first.getAttribute('data-title');
  assert.ok(title?.trim(), 'recomendaciones/: falta el título de la primera ficha');
  await search.fill(title);
  await page.waitForFunction(q => new URLSearchParams(location.hash.slice(1)).get('q') === q, title);
  const original = await root.locator('[data-catalogue-book]:visible').evaluateAll(nodes => nodes.map(n => n.dataset.bookId).sort());
  assert.ok(original.length, `recomendaciones/: la búsqueda ${title} no devuelve libros`);
  const url = page.url();
  const second = await context.newPage();
  await second.goto(url);
  await second.waitForFunction(q => document.querySelector('[data-filter="q"]')?.value === q, title);
  const restored = await second.locator('[data-reading-catalogue] [data-catalogue-book]:visible').evaluateAll(nodes => nodes.map(n => n.dataset.bookId).sort());
  assert.deepEqual(restored, original, `recomendaciones/: resultados diferentes al compartir ${url}`);
} finally {
  await context.close();
  await browser.close();
}