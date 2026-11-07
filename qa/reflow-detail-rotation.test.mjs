import test from 'node:test';
import assert from 'node:assert/strict';
import { rotateDetailRoutes, routeBucket } from './reflow-detail-rotation.mjs';

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

test('en K runs consecutivos se cubren todas las fichas, una vez cada una', () => {
  const seen = new Map();
  for (let day = 100; day < 107; day++) {
    const { routes } = rotateDetailRoutes(all, { k: 7, day, heaviest: 0 });
    routes.filter((r) => !fixed.includes(r)).forEach((r) => seen.set(r, (seen.get(r) || 0) + 1));
  }
  assert.equal(seen.size, books.length + authors.length);
  assert.ok([...seen.values()].every((n) => n === 1));
});

test('las altas no cambian la franja de las fichas existentes', () => {
  const grown = [...all, ...Array.from({ length: 300 }, (_, i) => `/recomendaciones/libros/a-nuevo-${i}/`)];
  for (let day = 0; day < 7; day++) {
    const before = rotateDetailRoutes(all, { k: 7, day, heaviest: 0 }).routes;
    const after = new Set(rotateDetailRoutes(grown, { k: 7, day, heaviest: 0 }).routes);
    for (const r of before) assert.ok(after.has(r), `${r} dia ${day}`);
  }
});

test('reparto aproximado a 1/K', () => {
  const many = Array.from({ length: 7000 }, (_, i) => `/recomendaciones/libros/libro-${i}-97884${i}/`);
  const counts = Array(7).fill(0);
  many.forEach((r) => counts[routeBucket(r, 7)]++);
  for (const c of counts) assert.ok(c > 850 && c < 1150, String(counts));
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
