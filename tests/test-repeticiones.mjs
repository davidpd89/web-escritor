import assert from 'node:assert/strict';
import { analyzeRepetitions } from '../assets/repeticiones-engine.js';

const sample = `Noa miró la puerta. La puerta seguía abierta y Noa volvió a mirar la puerta antes de entrar. Parecía tranquila. Parecía tranquila.`;
const res = analyzeRepetitions(sample, { windowSize: 30 });
assert.equal(res.empty, false);
assert(res.wordCount > 0);
assert(Array.isArray(res.echoes));
console.log('tests/test-repeticiones: OK');
