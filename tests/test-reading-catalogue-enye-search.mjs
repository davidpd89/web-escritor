import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import vm from 'node:vm';

const script = readFileSync('assets/reading-catalogue.js', 'utf8');
const page = readFileSync('recomendaciones/index.html', 'utf8');

// Extraer la función que realmente utiliza el catálogo, sin mantener
// una implementación alternativa que pudiera ocultar la regresión.
const declaration = script.match(/const normalize\s*=\s*s\s*=>\s*([^;]+);/);
assert.ok(declaration, 'No se encuentra la normalización del buscador');
const normalize = vm.runInNewContext(`(s => ${declaration[1]})`);

const cases = [
  { query: 'ano', title: 'año', expected: false },
  { query: 'pena', title: 'peña', expected: false },
  { query: 'canon', title: 'cañón', expected: false },
  { query: 'nino', title: 'niño', expected: false },
  { query: 'cafe', title: 'café', expected: true },
  { query: 'fantasia', title: 'fantasía', expected: true },
  { query: 'NINO', title: 'nino', expected: true },
  { query: 'NIÑO', title: 'niño', expected: true }
];

test('el catálogo publicado utiliza el módulo auditado', () => {
  assert.match(page, /<script[^>]+src="\/assets\/reading-catalogue\.js\?v=\d+"/);
  assert.match(script, /normalize\(card\.dataset\.search\)\.includes\(normalize\(v\.q\s*\|\|\s*''\)\)/);
});

for (const { query, title, expected } of cases) {
  test(`búsqueda ${JSON.stringify(query)} frente a ${JSON.stringify(title)}`, () => {
    const actual = normalize(title).includes(normalize(query));
    assert.equal(actual, expected, `El buscador confunde términos distintos: ${query} / ${title}`);
  });
}

test('la normalización conserva la distinción n/ñ en ambas direcciones', () => {
  assert.notEqual(normalize('n'), normalize('ñ'));
  assert.notEqual(normalize('N'), normalize('Ñ'));
  assert.equal(normalize('áéíóú'), normalize('aeiou'));
});
