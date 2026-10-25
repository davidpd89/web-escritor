import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = process.env.BASE_URL || process.env.SITE_URL || 'http://127.0.0.1:8000';
const browser = await chromium.launch();
try {
  const page = await browser.newPage();
  await page.goto(new URL('/recomendaciones/', base).href);
  await page.waitForFunction(() => !document.querySelector('[data-catalogue-filters] fieldset')?.disabled);
  const candidates = await page.locator('[data-catalogue-book]').evaluateAll(cards => {
    const values = new Map();
    for (const card of cards) for (const category of card.dataset.categories.split(' ')) values.set(category, (values.get(category) || 0) + 1);
    return [...document.querySelectorAll('input[data-facet="genero"]')].map(box => box.value).filter(value => values.has(value));
  });
  assert.ok(candidates.length >= 2, 'recomendaciones/: faltan dos géneros reales para comprobar la unión');
  const [a, b] = candidates;
  const ids = async () => page.locator('[data-catalogue-book]:visible').evaluateAll(nodes => nodes.map(n => n.dataset.bookId).sort());
  const checkbox = value => page.locator('input[data-facet="genero"]').filter({ has: page.locator('nonexistent') });
  const set = async (value, checked) => {
    await page.locator(`[data-facet="genero"][value="${value}"]`).evaluate((node, state) => { node.checked = state; node.dispatchEvent(new Event('change', { bubbles: true })); }, checked);
    await page.waitForFunction(([v, state]) => new URLSearchParams(location.hash.slice(1)).getAll('genero').includes(v) === state, [value, checked]);
  };
  await set(a, true);
  const onlyA = await ids();
  await set(a, false);
  await set(b, true);
  const onlyB = await ids();
  await set(a, true);
  const combined = await ids();
  const expected = [...new Set([...onlyA, ...onlyB])].sort();
  assert.deepEqual(combined, expected, `recomendaciones/: unión incorrecta de géneros ${a} y ${b}`);
  await set(a, false);
  assert.deepEqual(await ids(), onlyB, `recomendaciones/: desmarcar ${a} altera los resultados de ${b}`);
} finally {
  await browser.close();
}