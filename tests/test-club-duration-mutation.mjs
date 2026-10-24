import assert from 'node:assert/strict';
import { buildSession } from '../assets/club-session-engine.js';

const invalid = [
  '', ' ', '0', '29', '31', '59', '61', '89', '91',
  '-30', '-90', '30.0001', '89.999', '90.01',
  'NaN', 'Infinity', '-Infinity', '1e9', '90foo',
  '0xFF', '999999999999999999999', null, undefined
];
const valid = ['30', 30, '60', 60, '90', 90];

for (const value of invalid) {
  const result = buildSession({ duration: value });
  assert.equal(result.duration, 60, `Valor inválido aceptado: ${String(value)}`);
  assert.equal(result.timing.opening + result.timing.core + result.timing.close, 60);
  assert.equal(result.questions.length, result.timing.questions);
}
for (const value of valid) {
  const result = buildSession({ duration: value });
  assert.equal(result.duration, Number(value));
  assert.equal(result.timing.opening + result.timing.core + result.timing.close, result.duration);
}
console.log('test-club-duration-mutation: OK');