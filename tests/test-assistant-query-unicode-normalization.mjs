import assert from 'node:assert/strict';
import { normalizeQuery, QUERY_MAX_LENGTH } from '../assets/assistant-core.mjs';

const cases = [
  ['  ¿Quién   es   David?  ', '¿Quién es David?'],
  ['¿Que\u0301 libro recomiendas?', '¿Qué libro recomiendas?'],
  ['  Samuel\nentre\tmundos  ', 'Samuel entre mundos'],
  ['Noveris\r\n  y fantasía', 'Noveris y fantasía'],
  ['   ', ''],
  ['a'.repeat(501), 'a'.repeat(500)]
];

for (const [input, expected] of cases) {
  assert.equal(normalizeQuery(input), expected);
}

for (const input of ['¿Qué es Noveris?', 'Las manecillas del recuerdo', 'Fantasía y ciencia ficción', 'a'.repeat(700), 'á'.repeat(250)]) {
  const normalized = normalizeQuery(input);
  assert.equal(normalizeQuery(normalized), normalized, `Normalización no idempotente: ${input.slice(0, 30)}`);
  assert.ok(normalized.length <= QUERY_MAX_LENGTH);
  assert.equal(normalized, normalized.normalize('NFC'));
}
console.log('assistant-query-unicode-normalization: OK');