// window.DPRadarDates (assets/radar-convocatorias.js) has zero regression
// coverage anywhere in the suite despite being real, pure date-civil-math
// logic (parseCivil/daysUntil/daysSince/relativeLabel) reused by both the
// per-card status text and the "closes soon" filter checkbox. It deliberately
// does all arithmetic in UTC millis (Date.UTC) specifically to sidestep
// local-timezone DST shifts, so this is exactly the kind of logic worth
// stress-testing at year/leap-year/DST-adjacent boundaries rather than
// trusting that the UTC-only design is bug-free by inspection alone.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const code = fs.readFileSync(path.join(__dirname, '../assets/radar-convocatorias.js'), 'utf8');
const sandbox = { window: {}, document: { querySelectorAll: () => [], querySelector: () => null, addEventListener: () => {} } };
vm.createContext(sandbox);
vm.runInContext(code, sandbox);
const { parseCivil, daysUntil, daysSince, relativeLabel } = sandbox.window.DPRadarDates;

// Basic validity / invalid-calendar-date rejection (e.g. 2027-02-29 does not exist)
assert.ok(parseCivil('2026-09-03'), 'fecha válida debe parsear');
assert.equal(parseCivil('2027-02-29'), null, '2027 no es bisiesto: 29 de febrero no existe');
assert.ok(parseCivil('2028-02-29'), '2028 sí es bisiesto: 29 de febrero es válido');
assert.equal(parseCivil('not-a-date'), null, 'texto no numérico debe rechazarse');
assert.equal(parseCivil('2026-13-01'), null, 'mes 13 no existe');

// Leap-day arithmetic: from 2028-02-28 to 2028-03-01 is 2 days (crossing Feb 29 in a leap year)
assert.equal(daysUntil('2028-03-01', '2028-02-28'), 2, 'debe contar el 29 de febrero en un año bisiesto');
// Same span the following (non-leap) year is only 1 day
assert.equal(daysUntil('2029-03-01', '2029-02-28'), 1, 'sin 29 de febrero, el mismo tramo es 1 día');

// Year-boundary arithmetic: Dec 31 -> Jan 1 must be exactly 1 day, not 0 or negative
assert.equal(daysUntil('2027-01-01', '2026-12-31'), 1, 'cruzar fin de año cuenta como 1 día, no 0');
assert.equal(daysUntil('2030-01-01', '2029-12-25'), 7, 'una semana que cruza el cambio de año sigue siendo 7 días');

// Century/leap-rule edge case: 2000 was a leap year (divisible by 400), 2100 will not be
assert.ok(parseCivil('2000-02-29'), '2000 es bisiesto (divisible por 400)');
assert.equal(parseCivil('2100-02-29'), null, '2100 no es bisiesto (divisible por 100 pero no por 400)');

// Symmetry: daysUntil and daysSince must agree on the same pair of dates
assert.equal(daysUntil('2026-09-10', '2026-09-03'), daysSince('2026-09-03', '2026-09-10'), 'daysUntil y daysSince deben ser simétricos');

// A deadline in the past yields a negative day count, not null or a clamp to 0
assert.equal(daysUntil('2026-01-01', '2026-09-03'), -245, 'un plazo ya pasado debe dar un número negativo real');

// relativeLabel boundary values
assert.equal(relativeLabel(0), 'hoy');
assert.equal(relativeLabel(1), 'mañana');
assert.equal(relativeLabel(2), 'faltan 2 días');
assert.equal(relativeLabel(-1), 'plazo finalizado');

console.log('tests/test-radar-dates: OK');
