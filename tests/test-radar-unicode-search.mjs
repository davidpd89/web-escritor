import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync('assets/radar-convocatorias.js', 'utf8');
const match = source.match(/const normalize = \(value = ''\) => ([\s\S]*?)\.trim\(\);/);
assert.ok(match, 'No se encuentra la función normalize del radar');
const normalize = vm.runInNewContext(`(value => ${match[1]}.trim())`);
const cases = [
  ['POESÍA', 'poesia', true],
  ['Narración', 'narracion', true],
  ['AÑO', 'ano', false],
  ['NIÑO', 'nino', false],
  ['PINGÜINO', 'pinguino', false],
  ['GÜE', 'gue', false],
  ['Cafe\u0301', 'café', true],
  ['  NOVELA  ', 'novela', true]
];
for (const [a, b, equivalent] of cases) {
  assert.equal(normalize(a) === normalize(b), equivalent, `Normalización incorrecta: ${a} / ${b}`);
}
console.log(`PASS: ${cases.length} casos Unicode del radar`);
