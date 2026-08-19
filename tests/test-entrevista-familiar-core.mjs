import assert from 'node:assert/strict';
import { buildInterviewPlan, THEMES } from '../assets/entrevista-familiar-core.js';

const fixed = () => 0;
const shortPlan = buildInterviewPlan({ duration: 15, themes: ['infancia'], objectMode: false }, fixed);
assert.equal(shortPlan.questions.length, 6);
assert.equal(shortPlan.questions[0].type, 'warmup');
assert.equal(shortPlan.questions.at(-1).type, 'closing');
assert.equal(shortPlan.hasSensitiveTheme, false);
assert.equal(shortPlan.followUps.length, 4);

const longPlan = buildInterviewPlan({ duration: 60, themes: ['dificil', 'familia'], objectMode: true }, fixed);
assert.equal(longPlan.questions.length, 18);
assert.equal(longPlan.hasSensitiveTheme, true);
assert.ok(longPlan.questions.some((q) => q.type === 'object'));
assert.ok(longPlan.questions.every((q) => typeof q.text === 'string' && q.text.length > 10));
assert.ok(THEMES.dificil.sensitive);

const defaultPlan = buildInterviewPlan({}, fixed);
assert.equal(defaultPlan.duration, 30);
assert.equal(defaultPlan.questions.length, 10);

for (const duration of [15, 30, 45, 60]) {
  const expected = ({ 15: 6, 30: 10, 45: 14, 60: 18 })[duration];
  const plan = buildInterviewPlan({ duration, themes: ['trabajo'], objectMode: false }, fixed);
  assert.equal(plan.questions.length, expected, `duration ${duration}`);
}

console.log('tests/test-entrevista-familiar-core: OK');
