import test from 'node:test';
import assert from 'node:assert/strict';
import { rotateDetailRoutes } from './reflow-detail-rotation.mjs';

const books = Array.from({ length: 70 }, (_, i) => `/recomendaciones/libros/l${String(i).padStart(3, '0')}/`);
const authors = Array.from({ length: 21 }, (_, i) => `/recomendaciones/autores/a${String(i).padStart(3, '0')}/`);
const fixed = ['/', '/recomendaciones/', '/recomendaciones/libros/', '/recomendaciones/pagina/2/', '/blog/x/'];
const all = [...fixed, ...books, ...authors];
const size = (r) => (r.endsWith('l069/') ? 9e6 : r.length);

test('sin rotacion (K<=1) devuelve todas las rutas', () => {
  assert.equal(rotateDetailRoutes(all, { k: 1, day: 3 }).routes.length, all.length);
  assert.equal(rotateDetailRoutes(all, { k: NaN, day: 3 }).routes.length, all.length);
});

test('las paginas que no son ficha se recorren siempre', () => {
  for (let day = 0; day < 7; day++) {
    const { routes } = rotateDetailRoutes(all, { k: 7, day, heaviest: 0 });
    for (const r of fixed) assert.ok(routes.includes(r), `${r} dia ${day}`);
  }
});

test('en K dias se cubren todas las fichas y cada dia es ~1/K', () => {
  const seen = new Set();
  for (let day = 100; day < 107; day++) {
    const { routes, kinds } = rotateDetailRoutes(all, { k: 7, day, heaviest: 0 });
    assert.equal(kinds.libros.audited, 10);
    assert.equal(kinds.autores.audited, 3);
    routes.forEach((r) => seen.add(r));
  }
  assert.equal(seen.size, all.length);
});

test('las fichas mas pesadas entran todos los dias', () => {
  for (let day = 0; day < 7; day++) {
    const { routes } = rotateDetailRoutes(all, { k: 7, day, heaviest: 1, sizeOf: size });
    assert.ok(routes.includes('/recomendaciones/libros/l069/'));
  }
});

test('el resultado no depende del orden de entrada', () => {
  const a = rotateDetailRoutes(all, { k: 7, day: 5, heaviest: 2, sizeOf: size }).routes;
  const b = rotateDetailRoutes([...all].reverse(), { k: 7, day: 5, heaviest: 2, sizeOf: size }).routes;
  assert.deepEqual(a, b);
});
