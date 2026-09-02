import assert from 'node:assert/strict';
import { analyzeText } from '../assets/legibilidad-engine.js';
const sample = 'Esto es una frase. «Diálogo breve» y otra frase con más palabras que la anterior.';
const res = analyzeText(sample);
assert.equal(res.empty, false);
assert.equal(typeof res.inflesz.score, 'number');
assert.equal(res.wordCount > 0, true);

// Regression (2026-09-02): below the reliable-sample floor, the four
// "per 100 words" formulas produced actively nonsensical output instead of
// declining to score -- e.g. Crawford (a school-grade-level estimate) went
// negative for a 2-word input with no period, and an unrelated 2-token
// number string scored identically to it across all four formulas. The
// per-paragraph rows already had a "Muestra corta" guard for this same
// failure mode; this checks it now also applies to the whole-document
// scores, not only there.
const short = analyzeText('hola mundo');
assert.equal(short.reliableSample, false, 'a 2-word, unpunctuated sample must not be treated as reliable');
assert.equal(short.crawford.score, null, 'Crawford must not return a value for a sample this short');
assert.equal(short.crawford.label, 'Muestra corta');
assert.equal(short.inflesz.score, null);
assert.equal(short.fernandezHuerta.score, null);
assert.equal(short.gutierrez.score, null);

const onePunctuatedWord = analyzeText('Sí.');
assert.equal(onePunctuatedWord.reliableSample, false, 'a single punctuated word is exactly as degenerate as an unpunctuated one');

console.log('tests/test-legibilidad: OK');
