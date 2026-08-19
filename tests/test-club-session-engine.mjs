import assert from 'node:assert/strict';
import { buildSession } from '../assets/club-session-engine.js';

// Same input -> same output (deterministic, seeded by config), so a
// reader who reloads the page gets a stable session rather than a
// different one on every visit.
const config = { title: 'Samuel entre mundos', author: 'David Porto Díaz', kind: 'fiction', genre: 'fantasy', tone: 'balanced', duration: 60, scope: 'complete' };
const a = buildSession(config, 0);
const b = buildSession(config, 0);
assert.deepEqual(a, b);

// Duration controls timing allocation and question count.
const short = buildSession({ ...config, duration: 30 }, 0);
assert.equal(short.timing.opening, 5);
assert.equal(short.timing.activity, false);
assert.equal(short.activity, null);
assert.equal(short.questions.length, short.timing.questions);
assert.equal(short.opening.length, 1);

const long = buildSession({ ...config, duration: 90 }, 0);
assert.equal(long.timing.activity, true);
assert.ok(long.activity);
assert.equal(long.opening.length, 2);
assert.equal(long.closing.length, 2);

// A different "variant" (the "otra combinación" button) changes the
// selection without changing the config.
const variant1 = buildSession(config, 1);
assert.notDeepEqual(a.questions, variant1.questions);

// Partial-read scope avoids ending-focused questions.
const partial = buildSession({ ...config, scope: 'partial' }, 0);
for (const q of partial.questions) {
  assert.ok(!/final|terminar|terminaste|llegar al final|principio y el final|cierre/i.test(q), q);
}

// Custom tokens (character/theme names) generate extra tailored questions.
const withTokens = buildSession({ ...config, tokens: 'memoria, familia' }, 0);
const withoutTokens = buildSession({ ...config, tokens: '' }, 0);
assert.notDeepEqual(withTokens.questions, withoutTokens.questions);

// No duplicate questions within a single generated session.
const unique = new Set(a.questions);
assert.equal(unique.size, a.questions.length);

console.log('tests/test-club-session-engine: OK');
