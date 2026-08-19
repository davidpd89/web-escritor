import assert from 'node:assert/strict';
import { calculateReadAloud, countWords, formatDuration } from '../assets/tiempo-lectura-voz-alta.js';

// Word counting
assert.equal(countWords('Hola mundo, ¿qué tal estás?'), 5);
assert.equal(countWords(''), 0);

// No input -> zeroed result, no throw
const empty = calculateReadAloud({});
assert.equal(empty.words, 0);
assert.equal(empty.minutes, 0);
assert.deepEqual(empty.quickBudgets, []);

// Manual word count, default speed (155 wpm) and buffer (0%)
const manual = calculateReadAloud({ manualWords: 1550, wpm: 155, bufferPct: 0, targetMinutes: 5 });
assert.equal(manual.words, 1550);
assert.equal(manual.minutes, 10); // 1550 / 155 = 10 min exactly
assert.equal(manual.duration, '10 min 0 s');
assert.equal(manual.maxWordsForTarget, 775); // 5 min * 155 wpm
assert.equal(manual.effectiveWpm, 155);
assert.equal(manual.quickBudgets.length, 4);
assert.equal(manual.quickBudgets[1].minutes, 5);
assert.equal(manual.quickBudgets[1].words, 775);

// Pause buffer increases duration and lowers effective speed / capacity
const buffered = calculateReadAloud({ manualWords: 1550, wpm: 155, bufferPct: 10, targetMinutes: 5 });
assert.equal(buffered.words, 1550);
assert.ok(buffered.minutes > manual.minutes);
assert.ok(buffered.maxWordsForTarget < manual.maxWordsForTarget);
assert.ok(buffered.effectiveWpm < 155);

// Typed text takes precedence over manualWords when both are present
const withText = calculateReadAloud({ text: 'uno dos tres', manualWords: 9999, wpm: 155 });
assert.equal(withText.words, 3);

// Inputs are clamped to sane ranges
const clamped = calculateReadAloud({ manualWords: 100, wpm: 1000, bufferPct: -5, targetMinutes: -1 });
assert.equal(clamped.effectiveWpm, 300); // wpm clamped to max 300, bufferPct clamped to 0

// formatDuration edge cases
assert.equal(formatDuration(0), '0 s');
assert.equal(formatDuration(1.5), '1 min 30 s');
assert.equal(formatDuration(61), '1 h 1 min 0 s');

console.log('tests/test-tiempo-lectura-voz-alta: OK');
