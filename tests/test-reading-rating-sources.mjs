// Fuentes de valoración que pinta el catálogo: cada una con su dominio y su ruta, y nada más.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import vm from 'node:vm';
import test from 'node:test';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const source = readFileSync(resolve(root, 'assets/reading-catalogue.js'), 'utf8').replace(/\r\n/g, '\n');
const start = source.indexOf('  const stamp = ');
const end = source.indexOf('  const thinRating = ');
assert.ok(start !== -1 && end > start, 'Validadores de valoración no localizables en reading-catalogue.js');
const { validRating, ratingLabel } = vm.runInNewContext(
  '(() => {' + source.slice(start, end) + '; return { validRating, ratingLabel }; })()', { URL, Date, Number });

const now = Date.now();
const iso = ms => new Date(ms).toISOString().replace(/\.\d{3}Z$/, 'Z');
const rating = extra => ({ libro_id: 'b', puntuacion: 4.4, numero_valoraciones: 1280,
  actualizado_en: iso(now - 86400000), caduca_en: iso(now + 29 * 86400000), ...extra });

test('las estrellas de la ficha de Amazon se pintan con su enlace a las opiniones', () => {
  const r = rating({ fuente: 'amazon', url: 'https://www.amazon.es/dp/8498382378?tag=davidporto-21#customerReviews' });
  assert.equal(validRating(r), true);
  assert.equal(ratingLabel(r), 'Amazon');
});

test('una nota de Amazon fuera de su dominio o de una ficha no se pinta', () => {
  for (const url of ['https://www.amazon.com/dp/8498382378', 'https://amazon.es.fake.test/dp/8498382378',
    'http://www.amazon.es/dp/8498382378', 'https://www.amazon.es/s?k=coraline', 'https://www.amazon.es/dp/coraline'])
    assert.equal(validRating(rating({ fuente: 'amazon', url })), false, url);
});

test('las demás fuentes siguen igual', () => {
  assert.equal(ratingLabel(rating({ fuente: 'goodreads' })), 'Goodreads');
  assert.equal(validRating(rating({ fuente: 'goodreads', url: 'https://www.goodreads.com/book/show/123-x' })), true);
  assert.equal(validRating(rating({ fuente: 'inventada', url: 'https://www.goodreads.com/book/show/123-x' })), false);
  assert.equal(validRating(rating({ fuente: 'amazon', url: 'https://www.amazon.es/dp/8498382378', numero_valoraciones: 3 })), false);
});
