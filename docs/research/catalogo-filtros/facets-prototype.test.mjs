// Pruebas unitarias autocontenidas del prototipo (NO conectadas a Actions).
// Ejecutar cuando se quiera: node --test docs/research/catalogo-filtros/facets-prototype.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { calculateFacetOptions, activeFilters } from './facets-prototype.mjs';

const books = [
  { id: 'a', group: 'cocina', categories: ['cocina', 'adultos'], title: 'Recetas de otoño' },
  { id: 'b', group: 'cocina', categories: ['cocina', 'adultos'], title: 'Recetas de verano' },
  { id: 'c', group: 'novela', categories: ['fantasia', 'adultos'], title: 'El portal' },
  { id: 'd', group: 'novela', categories: ['terror', 'adultos'], title: 'Medianoche' },
  { id: 'e', group: 'infantil', categories: ['infantil', 'juvenil'], title: 'Páginas mágicas' }
];
const match = (book, state) =>
  (!state.grupo || book.group === state.grupo) &&
  (!state.genero || book.categories.includes(state.genero)) &&
  (!state.q || book.title.toLowerCase().includes(state.q.toLowerCase()));

const genres = [
  { value: '', label: 'Todos los géneros' },
  { value: 'cocina', label: 'Cocina' },
  { value: 'fantasia', label: 'Fantasía' },
  { value: 'terror', label: 'Terror' },
  { value: 'infantil', label: 'Infantil' }
];
const groups = [
  { value: '', label: 'Todos' },
  { value: 'cocina', label: 'Cocina' },
  { value: 'novela', label: 'Novela' },
  { value: 'infantil', label: 'Infantil' }
];
const options = (facet, selected, choices) =>
  calculateFacetOptions({ records: books, selected, facet, choices, match });

test('tipo Cocina limita los géneros del segundo filtro', () => {
  const result = options('genero', { grupo: 'cocina' }, genres);
  assert.deepEqual(result.map(o => o.value), ['', 'cocina']);
  assert.equal(result.find(o => o.value === 'cocina').count, 2);
});

test('al cambiar Género se excluye solo su propia restricción', () => {
  const result = options('genero', { grupo: 'novela', genero: 'fantasia' }, genres);
  assert.deepEqual(result.map(o => o.value), ['', 'fantasia', 'terror']);
  assert.equal(result.find(o => o.value === 'terror').count, 1);
});

test('selección antigua incompatible nunca desaparece silenciosamente', () => {
  const result = options('genero', { grupo: 'cocina', genero: 'terror' }, genres);
  assert.deepEqual(result.map(o => o.value), ['', 'cocina', 'terror']);
  assert.equal(result.find(o => o.value === 'terror').count, 0);
  assert.equal(result.find(o => o.value === 'terror').selected, true);
});

test('contadores de Tipo reaccionan a un Género seleccionado', () => {
  const result = options('grupo', { genero: 'fantasia' }, groups);
  assert.deepEqual(result.map(o => o.value), ['', 'novela']);
  assert.equal(result.find(o => o.value === 'novela').count, 1);
});

test('buscar texto recalcula opciones sin comprometer categoría activa', () => {
  const result = options('genero', { grupo: 'cocina', q: 'otoño' }, genres);
  assert.deepEqual(result.map(o => [o.value, o.count]), [['', 1], ['cocina', 1]]);
});

test('un chip elimina solo su restricción, no la búsqueda ni la ordenación', () => {
  const chips = activeFilters({ q: 'Recetas', grupo: 'cocina', orden: 'titulo' }, (key, value) => key + ': ' + value);
  assert.equal(chips.length, 2);
  assert.deepEqual(chips.find(c => c.key === 'grupo').next, { q: 'Recetas', grupo: '', orden: 'titulo' });
});

test('sin resultados mantiene la opción general y la opción seleccionada', () => {
  const result = options('genero', { q: 'NO EXISTE', genero: 'fantasia' }, genres);
  assert.deepEqual(result.map(o => [o.value, o.count]), [['', 0], ['fantasia', 0]]);
});
