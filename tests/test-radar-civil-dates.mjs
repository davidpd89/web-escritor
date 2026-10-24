import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync('assets/radar-convocatorias.js', 'utf8');
const context = {
  window: {},
  document: { querySelectorAll: () => [] },
  Intl, Date, Object, Number, String, Math
};
vm.runInNewContext(source, context);
const dates = context.window.DPRadarDates;
assert.ok(dates, 'No se exportan las utilidades de fecha');
assert.equal(dates.SITE_TIME_ZONE, 'Europe/Madrid');
for (const invalid of ['2026-02-29', '2026-04-31', '2026-13-01', '2026-00-10', '2026-01-00', '2026-1-1', 'texto']) {
  assert.equal(dates.parseCivil(invalid), null, `Fecha inválida aceptada: ${invalid}`);
}
assert.ok(dates.parseCivil('2028-02-29'));
const cases = [
  ['2026-03-29', '2026-03-28', 1],
  ['2026-03-30', '2026-03-29', 1],
  ['2026-10-25', '2026-10-24', 1],
  ['2026-10-26', '2026-10-25', 1],
  ['2028-03-01', '2028-02-28', 2],
  ['2026-01-01', '2025-12-31', 1],
  ['2026-10-23', '2026-10-24', -1]
];
for (const [deadline, today, expected] of cases) {
  assert.equal(dates.daysUntil(deadline, today), expected, `${today} -> ${deadline}`);
}
assert.equal(dates.relativeLabel(0), 'hoy');
assert.equal(dates.relativeLabel(1), 'mañana');
assert.equal(dates.relativeLabel(-1), 'plazo finalizado');
assert.equal(dates.siteCivilDate('2026-10-24T22:30:00Z').day, 25);
assert.equal(dates.siteCivilDate('2026-03-28T23:30:00Z').day, 29);
console.log('PASS: calendario civil, DST y fechas límite');
