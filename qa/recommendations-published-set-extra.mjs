import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';

const base = process.env.RECOMMENDATIONS_BASE_URL || 'http://127.0.0.1:4173';
const data = JSON.parse(await fs.readFile('data/reading-catalogue.json', 'utf8'));
const expected = data.libros.filter(x => x.estado === 'publicado').map(x => String(x.id)).sort();
assert(expected.length > 0, 'Oráculo vacío');
assert.equal(new Set(expected).size, expected.length, 'Identidades duplicadas en origen');
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  await page.goto(base + '/recomendaciones/');
  const actual = await page.locator('[data-catalogue-book]').evaluateAll(nodes => nodes.map(x => x.dataset.bookId).sort());
  assert(actual.length > 0, 'No se encontraron tarjetas');
  assert(actual.every(Boolean), 'Tarjetas sin identidad');
  assert.equal(new Set(actual).size, actual.length, 'Tarjetas duplicadas');
  assert.deepEqual(actual, expected, 'Diferencia bidireccional entre datos y DOM');
} finally {
  await browser.close();
}