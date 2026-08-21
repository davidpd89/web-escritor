import assert from 'node:assert/strict';
import { validateEventModel, buildEventOutputs, foldIcsLine, escapeIcs, parseOffsetDate } from '../assets/evento-escritor-core.js';

const base = {
  name: 'Presentación de «La memoria»', url: 'https://autora.example/eventos/presentacion/',
  description: 'Charla, firma y preguntas.', venueName: 'Librería Central', streetAddress: 'Calle Mayor 1',
  addressLocality: 'Madrid', postalCode: '28001', addressRegion: 'Madrid', addressCountry: 'ES',
  allDay: false, startDateTime: '2026-09-03T19:00', endDateTime: '2026-09-03T20:30', utcOffset: '+02:00',
  confirmed: true,
};

assert.equal(validateEventModel(base).length, 0);

for (const patch of [
  { confirmed: false }, { url: 'http://x.test/' }, { utcOffset: 'Europe/Madrid' },
  { utcOffset: '+15:00' }, { endDateTime: '2026-09-03T18:00' },
  { startDateTime: '2026-02-31T19:00' }, { startDateTime: '2026-09-03T24:00' },
]) {
  assert.ok(validateEventModel({ ...base, ...patch }).length > 0, `expected invalid: ${JSON.stringify(patch)}`);
}

const out = buildEventOutputs(base);
assert.ok(out.jsonLd.includes('EventScheduled'));
assert.ok(out.jsonLd.includes('PostalAddress'));

const hostile = buildEventOutputs({ ...base, name: 'Cierre </script><script>alert(1)</script>' });
assert.ok(!hostile.jsonLd.includes('</script>'));
assert.ok(!hostile.html.includes('<script'));

assert.ok(out.ics.includes('DTSTART:20260903T170000Z'));
assert.ok(out.ics.includes('DTEND:20260903T183000Z'));

const allDayEvt = buildEventOutputs({ ...base, allDay: true, startDate: '2026-09-03', endDate: '2026-09-04', startDateTime: '', endDateTime: '', utcOffset: '' });
assert.ok(allDayEvt.ics.includes('DTSTART;VALUE=DATE:20260903'));
assert.ok(allDayEvt.ics.includes('DTEND;VALUE=DATE:20260905')); // exclusive end

for (const patch of [
  { startDate: '2026-02-31', endDate: '' },
  { startDate: '2026-02-28', endDate: '2026-02-31' },
]) {
  const invalidAllDay = { ...base, allDay: true, startDate: '2026-09-03', endDate: '', startDateTime: '', endDateTime: '', utcOffset: '', ...patch };
  assert.ok(validateEventModel(invalidAllDay).length > 0, `expected invalid all-day date: ${JSON.stringify(patch)}`);
}
const leapDay = { ...base, allDay: true, startDate: '2028-02-29', endDate: '', startDateTime: '', endDateTime: '', utcOffset: '' };
assert.equal(validateEventModel(leapDay).length, 0);

const long = foldIcsLine('DESCRIPTION:' + 'á'.repeat(100));
for (const line of long.split('\r\n')) {
  assert.ok(new TextEncoder().encode(line).length <= 75, `line too long: ${line}`);
}

assert.equal(escapeIcs('a,b;c\\d\ne'), 'a\\,b\\;c\\\\d\\ne');
assert.equal(escapeIcs('a\rb\r\nc\nd'), 'a\\nb\\nc\\nd');
assert.equal(parseOffsetDate('2026-09-03T19:00', '+02:00').toISOString(), '2026-09-03T17:00:00.000Z');

console.log('tests/test-evento-escritor-core: OK');
