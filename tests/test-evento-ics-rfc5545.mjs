// Gate 6 del doc 37: "importar .ics en Apple Calendar, Google Calendar y
// Outlook". No puedo abrir esas aplicaciones desde este entorno, asi que la
// verificacion equivalente es que el .ics cumpla RFC 5545, que es lo que esos
// clientes parsean. Este test comprueba el contrato estructural; ademas se
// valido fuera de banda con la libreria icalendar de Python (implementacion
// independiente): parseo correcto, DTSTART 19:00+02:00 -> 17:00Z, 0 lineas de
// mas de 75 octetos, CRLF, y descripcion desplegada identica con tildes y ñ.
import assert from 'node:assert/strict';
import { buildEventOutputs, foldIcsLine } from '../assets/evento-escritor-core.js';

const model = {
  name: 'Presentación de Las manecillas del recuerdo',
  confirmed: true,
  allDay: false,
  startDateTime: '2026-09-03T19:00',
  endDateTime: '2026-09-03T20:30',
  utcOffset: '+02:00',
  venueName: 'Librería de ejemplo — acentos: ñ á é ü',
  streetAddress: 'Calle Mayor 1',
  addressLocality: 'Madrid',
  addressRegion: 'Madrid',
  postalCode: '28013',
  addressCountry: 'España',
  url: 'https://davidportodiaz.com/eventos.html',
  description: 'Presentación con lectura de fragmentos; línea deliberadamente larga para forzar el plegado a 75 octetos y comprobar que al desplegar se reconstruye exactamente el texto original, incluidas las tildes y la ñ.',
};

const { ics, jsonLd } = buildEventOutputs(model);

// --- RFC 5545 ---
assert.ok(ics.startsWith('BEGIN:VCALENDAR'), 'debe empezar por BEGIN:VCALENDAR');
assert.ok(ics.trimEnd().endsWith('END:VCALENDAR'), 'debe terminar por END:VCALENDAR');
assert.match(ics, /\r\n/, 'RFC 5545 exige CRLF');
for (const prop of ['VERSION:2.0', 'PRODID:', 'BEGIN:VEVENT', 'UID:', 'DTSTAMP:', 'DTSTART:', 'END:VEVENT']) {
  assert.ok(ics.includes(prop), `falta la propiedad obligatoria ${prop}`);
}

// Plegado: ninguna linea puede exceder 75 OCTETOS (no caracteres)
for (const line of ics.split('\r\n')) {
  const octets = Buffer.byteLength(line, 'utf8');
  assert.ok(octets <= 75, `linea de ${octets} octetos supera el limite de 75: ${line.slice(0, 40)}…`);
}

// Desplegar (unfold) debe reconstruir el texto original con acentos intactos
const unfolded = ics.replace(/\r\n[ \t]/g, '');
assert.ok(unfolded.includes('tildes y la ñ'), 'el desplegado debe conservar los acentos');

// La conversion horaria debe ser real: 19:00 en +02:00 son las 17:00 UTC
assert.ok(unfolded.includes('DTSTART:20260903T170000Z'), 'DTSTART debe estar en UTC (17:00Z)');
assert.ok(unfolded.includes('DTEND:20260903T183000Z'), 'DTEND debe estar en UTC (18:30Z)');

// --- JSON-LD: requisitos documentados de Google para rich results de Event ---
const ld = typeof jsonLd === 'string' ? JSON.parse(jsonLd) : jsonLd;
assert.equal(ld['@context'], 'https://schema.org');
assert.equal(ld['@type'], 'Event');
for (const key of ['name', 'startDate', 'location']) {
  assert.ok(ld[key], `Event requiere ${key} para resultados enriquecidos`);
}
assert.equal(ld.location['@type'], 'Place');
assert.equal(ld.location.address['@type'], 'PostalAddress');
for (const key of ['streetAddress', 'addressLocality', 'addressCountry']) {
  assert.ok(ld.location.address[key], `PostalAddress requiere ${key}`);
}
assert.equal(ld.eventStatus, 'https://schema.org/EventScheduled');

// Adversarial line-folding (2026-09 audit round): the accented characters
// above (ñ, á, é, ü) are all 2-byte UTF-8, the easy case. foldIcsLine()
// iterates Array.from(String(line)) so it walks whole code points (correctly
// treating a surrogate pair as one unit) and checks TextEncoder byte length
// before deciding to fold -- but that combination is worth stress-testing
// directly against 3-byte (CJK) and 4-byte (emoji, surrogate-pair) UTF-8
// repeated across many fold boundaries, not just present once in a longer
// string, to catch an off-by-one that only shows up at a boundary.
function checkFoldRoundtrip(line) {
  const folded = foldIcsLine(line);
  for (const seg of folded.split('\r\n')) {
    assert.ok(Buffer.byteLength(seg, 'utf8') <= 75, `segmento de ${Buffer.byteLength(seg, 'utf8')} octetos supera 75: ${seg}`);
  }
  assert.equal(folded.replace(/\r\n /g, ''), line, 'desplegar debe reconstruir el texto original exacto');
}
checkFoldRoundtrip('DESCRIPTION:' + '📚'.repeat(40)); // 4-byte UTF-8 (surrogate pair), repeated across many folds
checkFoldRoundtrip('DESCRIPTION:' + '文'.repeat(40)); // 3-byte UTF-8, repeated across many folds
checkFoldRoundtrip('DESCRIPTION:' + 'a'.repeat(73) + '📚📚📚📚'); // ASCII run landing exactly at the fold boundary, then emoji
checkFoldRoundtrip('DESCRIPTION:' + 'a'.repeat(74) + '文文文文'); // same, one byte off, for CJK

console.log('test-evento-ics-rfc5545: OK');
