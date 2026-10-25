import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = process.env.BASE_URL || process.env.SITE_URL || 'http://127.0.0.1:8000';
const browser = await chromium.launch();
try {
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.goto(new URL('/recomendaciones/', base).href);
  const root = page.locator('[data-reading-catalogue]');
  const nav = root.locator('[data-catalogue-pagination]');
  await nav.waitFor({ state: 'visible' });
  const ids = async p => p.locator('[data-reading-catalogue] [data-catalogue-book]:visible').evaluateAll(nodes => nodes.map(n => n.dataset.bookId));
  const first = await ids(page);
  assert.ok(first.length > 0 && first.length <= 24, 'recomendaciones/: tamaño incorrecto de la primera página');
  await nav.getByRole('button', { name: /Siguiente/ }).click();
  await page.waitForFunction(() => new URLSearchParams(location.hash.slice(1)).get('pagina') === '2');
  const second = await ids(page);
  assert.ok(second.length > 0 && second.length <= 24, 'recomendaciones/: segunda página vacía o superior a 24 libros');
  assert.equal(first.filter(id => second.includes(id)).length, 0, 'recomendaciones/: fichas duplicadas entre páginas 1 y 2');
  const other = await context.newPage();
  await other.goto(page.url());
  await other.waitForFunction(() => document.querySelector('[data-catalogue-pagination]')?.textContent?.includes('Página 2'));
  assert.deepEqual(await ids(other), second, 'recomendaciones/: la URL de página 2 restaura otras fichas');
  await context.close();
} finally {
  await browser.close();
}