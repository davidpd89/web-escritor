import assert from 'node:assert/strict';
import fs from 'node:fs';

const js = fs.readFileSync('assets/assistant.js', 'utf8');
const html = fs.readFileSync('asistente/index.html', 'utf8');

assert.match(js, /\.normalize\(['\"]NFC['\"]\)/, 'Canonical Unicode normalization missing');
assert.match(js, /\.replace\(\/\\s\+\/g,\s*['\"] ['\"]\)/, 'Whitespace collapse missing');
assert.match(js, /rawQuery\.length\s*>\s*QUERY_MAX_LENGTH/, 'Length guard missing');
assert.match(html, /maxlength=['\"]500['\"]/, 'HTML limit differs from the expected public contract');

function normalize(value) {
  return String(value).normalize('NFC').replace(/\s+/g, ' ').trim();
}

const cases = [
  ['¿Dónde está el capítulo?', '¿Do\u0301nde esta\u0301 el capi\u0301tulo?'],
  ['¿Qué libros hay?', '  ¿Qué   libros\n hay?  '],
  ['Las manecillas del recuerdo', 'Las\tmanecillas\r\ndel recuerdo'],
];

for (const [expected, variant] of cases) {
  assert.equal(normalize(variant), expected, `Normalization drift: ${variant}`);
}

for (const length of [0, 1, 2, 499, 500, 501, 1000]) {
  const query = 'x'.repeat(length);
  assert.equal(normalize(query).length > 500, length > 500, `Boundary ${length}`);
}

assert.equal(normalize('x'.repeat(250) + ' '.repeat(300) + 'y'.repeat(249)).length, 500);
assert.equal(normalize('x'.repeat(500) + ' '.repeat(300) + 'y').length, 502);

console.log('assistant-query-normalization: OK');
