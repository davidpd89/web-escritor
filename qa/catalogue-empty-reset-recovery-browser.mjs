import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = process.env.BASE_URL || process.env.SITE_URL || 'http://127.0.0.1:8000';
const browser = await chromium.launch();
try {
  const page = await browser.newPage();
  await page.goto(new URL('/recomendaciones/', base).href);
  const root = page.locator('[data-reading-catalogue]');
  const search = root.locator('[data-filter="q"]');
  await page.waitForFunction(() => !document.querySelector('[data-catalogue-filters] fieldset')?.disabled);
  const initial = await root.locator('[data-catalogue-book]:visible').count();
  assert.ok(initial > 0, 'recomendaciones/: catálogo inicial sin fichas');
  const absent = 'zzzzzzzzzzzzzzzzzzzzzz';
  await search.fill(absent);
  await root.locator('[data-catalogue-empty]').waitFor({ state: 'visible' });
  assert.equal(await root.locator('[data-catalogue-book]:visible').count(), 0, 'recomendaciones/: la búsqueda sin coincidencias conserva fichas visibles');
  await root.locator('[data-catalogue-filters] [type="reset"]').click();
  await page.waitForFunction(() => document.querySelector('[data-filter="q"]')?.value === '' && !location.hash.includes('zzzz'));
  await root.locator('[data-catalogue-empty]').waitFor({ state: 'hidden' });
  assert.equal(await root.locator('[data-catalogue-book]:visible').count(), initial, 'recomendaciones/: el reinicio no recupera las fichas iniciales');
} finally {
  await browser.close();
}