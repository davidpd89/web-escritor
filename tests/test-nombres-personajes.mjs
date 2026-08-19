import assert from 'node:assert/strict';
import { analyze } from '../assets/nombres-personajes-engine.js';

const sample = ['Noa', 'Noah', 'Noa Díaz', 'Brais', 'Braís'];
const res = analyze(sample);
assert.equal(res.names.length, 5);
assert(Array.isArray(res.pairs));
console.log('tests/test-nombres-personajes: OK');
