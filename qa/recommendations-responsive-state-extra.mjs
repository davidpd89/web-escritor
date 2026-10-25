import { chromium } from 'playwright';
import assert from 'node:assert/strict';

const base = process.env.RECOMMENDATIONS_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
try {
  const context = await browser.newContext({ viewport: { width: 390, height: 900 }, reducedMotion: 'reduce' });
  await context.route(/^https?:\/\/(?!127\.0\.0\.1(?::4173)?(?:\/|$))/, route => route.abort());
  const page = await context.newPage();
  await page.goto(base + '/recomendaciones/');
  const facet = page.locator('input[data-facet="grupo"]:not(:disabled)').first();
  assert(await facet.count(), 'No existe un filtro de grupo habilitado');
  await facet.check({ force: true });
  const selected = await facet.inputValue();
  const snapshot = async () => page.evaluate(() => ({
    selected: [...document.querySelectorAll('input[data-facet]:checked')].map(x => [x.dataset.facet, x.value]).sort(),
    matches: [...document.querySelectorAll('[data-catalogue-book]')].filter(x => !x.hidden).map(x => x.dataset.bookId).sort()
  }));
  const initial = await snapshot();
  assert(initial.selected.some(x => x[1] === selected));
  for (const width of [320, 768, 1440, 390]) {
    await page.setViewportSize({ width, height: 900 });
    await page.evaluate(() => document.fonts.ready);
    assert.deepEqual(await snapshot(), initial, `Estado alterado a ${width}px`);
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `Desbordamiento a ${width}px`);
  }
  await context.close();
} finally {
  await browser.close();
}