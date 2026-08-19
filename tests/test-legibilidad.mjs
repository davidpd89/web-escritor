import assert from 'node:assert/strict';
import { analyzeText } from '../assets/legibilidad-engine.js';
const sample = 'Esto es una frase. «Diálogo breve» y otra frase con más palabras que la anterior.';
const res = analyzeText(sample);
assert.equal(res.empty, false);
assert.equal(typeof res.inflesz.score, 'number');
assert.equal(res.wordCount > 0, true);
console.log('tests/test-legibilidad: OK');
