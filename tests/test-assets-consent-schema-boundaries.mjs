import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync('assets/analytics-consent-banner.js', 'utf8');
const now = Date.UTC(2026, 9, 25, 12);
const maxAge = 24 * 30 * 24 * 60 * 60 * 1000;
const cases = [
  ['válido', { value: 'denied', v: 1, ts: now }, true],
  ['versión futura', { value: 'granted', v: 999, ts: now }, false],
  ['versión antigua', { value: 'granted', v: 0, ts: now }, false],
  ['fecha futura', { value: 'granted', v: 1, ts: now + 86400000 }, false],
  ['fecha negativa', { value: 'granted', v: 1, ts: -1 }, false],
  ['caducado', { value: 'granted', v: 1, ts: now - maxAge - 1 }, false],
  ['fecha cadena', { value: 'granted', v: 1, ts: String(now) }, false],
  ['valor desconocido', { value: 'accepted', v: 1, ts: now }, false],
  ['sin versión', { value: 'granted', ts: now }, false],
  ['sin fecha', { value: 'granted', v: 1 }, false]
];

for (const [label, stored, expected] of cases) {
  const storage = new Map([['dp-analytics-consent', JSON.stringify(stored)]]);
  const context = vm.createContext({
    Date: class extends Date { static now() { return now; } },
    localStorage: {
      getItem: key => storage.get(key) ?? null,
      setItem: (key, value) => storage.set(key, value)
    },
    window: {},
    document: {},
    console
  });
  vm.runInContext(source, context);
  const actual = vm.runInContext('getStoredAnalyticsConsent()', context);
  assert.equal(actual !== null, expected, label);
}
console.log('assets-consent-schema-boundaries: OK');
