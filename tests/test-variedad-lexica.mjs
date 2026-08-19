import assert from 'node:assert/strict';
import { analyzeLexicalDiversity, tokenizeSpanish } from '../assets/variedad-lexica-engine.js';

const text = 'Una casa vieja. Una casa nueva. Un coche. Un árbol.';
const tokens = tokenizeSpanish(text);
const res = analyzeLexicalDiversity(text);

assert(tokens.length > 0, 'tokenize should produce tokens');
assert(typeof res.tokenCount === 'number');
assert(Array.isArray(res.profile));
console.log('tests/test-variedad-lexica: OK');
