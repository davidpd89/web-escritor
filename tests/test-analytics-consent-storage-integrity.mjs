import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync('assets/analytics-consent-banner.js', 'utf8');
const values = new Map();
const sandbox = {
  window: {},
  document: { addEventListener() {} },
  localStorage: {
    getItem: key => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value)
  }
};
vm.createContext(sandbox);
vm.runInContext(source, sandbox);
const key = 'dp-analytics-consent';
const now = Date.now();
const maxAge = 24 * 30 * 24 * 60 * 60 * 1000;
const valid = { value: 'denied', v: 1, ts: now - 1000 };
values.set(key, JSON.stringify(valid));
assert.equal(sandbox.getStoredAnalyticsConsent().value, 'denied');
for (const payload of [
  { value: 'granted', v: 1, ts: -1 },
  { value: 'granted', v: 1, ts: now + 86400000 },
  { value: 'granted', v: 1, ts: now - maxAge - 1000 },
  { value: 'granted', v: 99, ts: now },
  { value: 'granted', ts: now },
  { value: 'other', v: 1, ts: now },
  { value: 'denied', v: 1, ts: null },
  { value: 'granted', v: 1, ts: '2026-01-01' }
]) {
  values.set(key, JSON.stringify(payload));
  assert.equal(sandbox.getStoredAnalyticsConsent(), null, `Consentimiento corrupto aceptado: ${JSON.stringify(payload)}`);
}
for (const malformed of ['{', '[]', 'null', 'false']) {
  values.set(key, malformed);
  assert.equal(sandbox.getStoredAnalyticsConsent(), null);
}
console.log('Analytics consent storage integrity: OK');