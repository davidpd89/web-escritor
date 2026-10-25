import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.RECOMMENDATIONS_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
const failures = [];
const cases = [
  { width: 1440, height: 900 },
  { width: 390, height: 844 },
  { width: 320, height: 568 },
  { width: 844, height: 390 },
  { width: 768, height: 1024 },
  { width: 1440, height: 900 }
];

try {
  const context = await browser.newContext({ viewport: cases[0], reducedMotion: 'reduce' });
  await context.route('**/*', route => {
    const url = new URL(route.request().url());
    return url.origin === new URL(BASE).origin ? route.continue() : route.abort();
  });
  const page = await context.newPage();
  await page.goto(BASE + '/recomendaciones/', { waitUntil: 'load' });
  const search = page.locator('[data-catalogue-filters] [data-filter="q"]');
  assert.equal(await search.count(), 1, 'Debe existir un buscador de catálogo');
  const candidate = await page.locator('[data-catalogue-book]').first().getAttribute('data-title');
  assert.ok(candidate, 'El catálogo debe contener libros');
  const term = candidate.slice(0, Math.min(8, candidate.length));
  await search.fill(term);
  await search.dispatchEvent('input');
  const baseline = await page.evaluate(() => ({
    matches: [...document.querySelectorAll('[data-catalogue-book]:not([hidden])')].map(e => e.dataset.bookId),
    count: document.querySelector('[data-catalogue-count]')?.textContent,
    query: document.querySelector('[data-filter="q"]')?.value
  }));
  assert.ok(baseline.matches.length > 0, 'La búsqueda debe encontrar libros');
  for (const vp of cases) {
    await page.setViewportSize(vp);
    const state = await page.evaluate(() => ({
      matches: [...document.querySelectorAll('[data-catalogue-book]:not([hidden])')].map(e => e.dataset.bookId),
      count: document.querySelector('[data-catalogue-count]')?.textContent,
      query: document.querySelector('[data-filter="q"]')?.value,
      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth
    }));
    try {
      assert.deepEqual(state.matches, baseline.matches);
      assert.equal(state.count, baseline.count);
      assert.equal(state.query, baseline.query);
      assert.ok(state.overflow <= 1, `Desbordamiento horizontal: ${state.overflow}px`);
    } catch (error) {
      failures.push(`${vp.width}x${vp.height}: ${error.message}`);
    }
  }
  await context.close();
  assert.deepEqual(failures, []);
} finally {
  await browser.close();
}
console.log('OK: transiciones responsivas del catálogo');