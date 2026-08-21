import assert from 'node:assert/strict';
import { calculateReadAloud, countWords, formatDuration } from '../assets/tiempo-lectura-voz-alta.js';

// Word counting
assert.equal(countWords('Hola mundo, ¿qué tal estás?'), 5);
assert.equal(countWords(''), 0);
assert.equal(countWords('  \n\t  '), 0);
assert.equal(countWords('—Hola— «mundo» ¿qué?\nTal vez, sí.'), 6);

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

// Controlled brief fixture: 930 words, 155 wpm, +10% pauses, 5 minutes.
// 930/155 = 6 minutes; pause factor 1.1 => 6.6 minutes = 6m36s.
const controlled = calculateReadAloud({ manualWords: 930, wpm: 155, bufferPct: 10, targetMinutes: 5 });
assert.equal(controlled.words, 930);
assert.ok(Math.abs(controlled.minutes - 6.6) < 1e-12);
assert.equal(controlled.duration, '6 min 36 s');
assert.equal(controlled.maxWordsForTarget, 704);
assert.ok(Math.abs(controlled.effectiveWpm - (155 / 1.1)) < 1e-9);

// Pause buffer increases duration and lowers effective speed / capacity
const buffered = calculateReadAloud({ manualWords: 1550, wpm: 155, bufferPct: 10, targetMinutes: 5 });
assert.equal(buffered.words, 1550);
assert.ok(buffered.minutes > manual.minutes);
assert.ok(buffered.maxWordsForTarget < manual.maxWordsForTarget);
assert.ok(buffered.effectiveWpm < 155);

// Typed text takes precedence over manualWords when both are present
const withText = calculateReadAloud({ text: 'uno dos tres', manualWords: 9999, wpm: 155 });
assert.equal(withText.words, 3);

// Inputs are clamped to documented ranges and output remains finite.
const extremes = [
  { manualWords: -10, wpm: 60, bufferPct: 0, targetMinutes: 0.5 },
  { manualWords: 100, wpm: 300, bufferPct: 100, targetMinutes: 600 },
  { manualWords: 100.9, wpm: 1000, bufferPct: -5, targetMinutes: -1 },
];
for (const input of extremes) {
  const result = calculateReadAloud(input);
  for (const value of [result.words, result.minutes, result.maxWordsForTarget, result.effectiveWpm]) {
    assert.ok(Number.isFinite(value), `${JSON.stringify(input)} produced ${value}`);
  }
}
const clamped = calculateReadAloud({ manualWords: 100, wpm: 1000, bufferPct: -5, targetMinutes: -1 });
assert.equal(clamped.effectiveWpm, 300); // wpm clamped to max 300, bufferPct clamped to 0

// formatDuration edge cases
assert.equal(formatDuration(0), '0 s');
assert.equal(formatDuration(1.5), '1 min 30 s');
assert.equal(formatDuration(61), '1 h 1 min 0 s');

console.log('tests/test-tiempo-lectura-voz-alta: OK');