import assert from 'node:assert/strict';
import { classifyIntentionalVisualHiding, reconcileTextResilience } from './text-resilience-report-gate.mjs';

assert.equal(classifyIntentionalVisualHiding({ selector: 'form > label.sr-only' }), 'sr-only-utility');
assert.equal(
  classifyIntentionalVisualHiding({ selector: 'div.site-header__left > button.header-search > span' }),
  'compact-header-search-label',
);
assert.equal(
  classifyIntentionalVisualHiding({ selector: 'h1.masthead__name.has-logo-image > a > span.masthead__name-text:nth-of-type(2)' }),
  'masthead-logo-text-fallback',
);
assert.equal(classifyIntentionalVisualHiding({ selector: 'div.card > p' }), null);

const reconciled = reconcileTextResilience({
  textResilience: {
    mode: 'report',
    checks: [
      {
        route: '/ok/',
        viewport: '320x900',
        scenario: 'resize-text-200',
        overflow: 0,
        offenders: [],
        clippedText: [{ selector: 'form > label.sr-only', hiddenX: 20, hiddenY: 10 }],
      },
      {
        route: '/overflow/',
        viewport: '320x900',
        scenario: 'resize-text-200',
        overflow: 3,
        offenders: [{ selector: 'main > div', overflow: 3 }],
        clippedText: [],
      },
      {
        route: '/clip/',
        viewport: '390x900',
        scenario: 'text-spacing',
        overflow: 0,
        offenders: [],
        clippedText: [{ selector: 'div.card > p', hiddenX: 4, hiddenY: 0 }],
      },
    ],
  },
});

assert.equal(reconciled.checkCount, 3);
assert.equal(reconciled.failureCount, 2);
assert.equal(reconciled.allowedVisualHiding['sr-only-utility'], 1);
assert.equal(reconciled.checks[0].failure, false);
assert.equal(reconciled.checks[1].failure, true);
assert.equal(reconciled.checks[2].failure, true);

console.log('text-resilience-report-gate.test: OK');
