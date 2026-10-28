import assert from 'node:assert/strict';
import test from 'node:test';
import {
  validateEventModel,
  buildEventOutputs,
} from '../assets/evento-escritor-core.js';

const base = {
  name: 'Firma de Samuel entre mundos',
  url: 'https://davidportodiaz.com/eventos.html#firma-madrid-turno-1',
  description: 'Primer turno de firmas',
  venueName: 'Feria del Libro de Madrid',
  streetAddress: 'Parque del Retiro',
  addressLocality: 'Madrid',
  addressCountry: 'ES',
  confirmed: true,
  allDay: false,
  startDateTime: '2026-06-10T19:00',
  endDateTime: '2026-06-10T20:00',
  utcOffset: '+02:00',
};

function generateValidated(model, label) {
  assert.deepEqual(
    validateEventModel(model),
    [],
    `${label}: el modelo debe superar validateEventModel()`,
  );
  return buildEventOutputs(model);
}

function uidOf(ics) {
  const unfolded = ics.replace(/\r\n[ \t]/g, '');
  const match = unfolded.match(/^UID:([^\r\n]+)$/m);
  assert.ok(match, 'El ICS debe contener un UID identificable');
  return match[1];
}

test('una URL distinta conserva fecha y horario, pero exige otro filename', () => {
  const changedUrl = {
    ...base,
    url: 'https://davidportodiaz.com/eventos.html#firma-madrid-turno-2',
  };

  const original = generateValidated(base, 'URL: original');
  const changed = generateValidated(changedUrl, 'URL: mutación');

  assert.equal(changedUrl.name, base.name);
  assert.equal(changedUrl.startDateTime, base.startDateTime);
  assert.equal(changedUrl.endDateTime, base.endDateTime);
  assert.equal(changedUrl.venueName, base.venueName);

  assert.notEqual(
    JSON.parse(original.jsonLd).url,
    JSON.parse(changed.jsonLd).url,
    'La transformación debe modificar la URL del evento',
  );
  assert.notEqual(
    uidOf(original.ics),
    uidOf(changed.ics),
    'Una URL distinta debe producir otro UID',
  );
  assert.notEqual(
    original.ics,
    changed.ics,
    'El ICS debe reflejar la nueva URL',
  );
  assert.notEqual(
    original.filename,
    changed.filename,
    'DEFECTO: dos URLs distintas con el mismo nombre, día y horario comparten filename',
  );
});

test('otra sesión horaria del mismo día exige otro filename', () => {
  const changedTime = {
    ...base,
    startDateTime: '2026-06-10T20:30',
    endDateTime: '2026-06-10T21:30',
  };

  const original = generateValidated(base, 'horario: original');
  const changed = generateValidated(changedTime, 'horario: mutación');

  assert.equal(changedTime.url, base.url);
  assert.equal(changedTime.name, base.name);
  assert.equal(changedTime.venueName, base.venueName);
  assert.equal(
    changedTime.startDateTime.slice(0, 10),
    base.startDateTime.slice(0, 10),
    'Ambas sesiones deben celebrarse el mismo día',
  );

  assert.notEqual(
    JSON.parse(original.jsonLd).startDate,
    JSON.parse(changed.jsonLd).startDate,
    'La transformación debe modificar el comienzo de la sesión',
  );
  assert.notEqual(
    uidOf(original.ics),
    uidOf(changed.ics),
    'Una sesión con otro comienzo debe producir otro UID',
  );
  assert.notEqual(
    original.ics,
    changed.ics,
    'El ICS debe reflejar el nuevo horario',
  );
  assert.notEqual(
    original.filename,
    changed.filename,
    'DEFECTO: dos sesiones con diferente horario del mismo día comparten filename',
  );
});

test('regenerar exactamente el mismo evento conserva su identidad de archivo', () => {
  const first = generateValidated(base, 'regeneración: primera salida');
  const second = generateValidated(base, 'regeneración: segunda salida');

  assert.equal(
    uidOf(first.ics),
    uidOf(second.ics),
    'Regenerar el mismo evento debe conservar su UID',
  );
  assert.equal(
    first.filename,
    second.filename,
    'Regenerar el mismo evento debe conservar su filename',
  );
});

test('un cambio exclusivamente descriptivo conserva UID y filename', () => {
  const changedDescription = {
    ...base,
    description: 'Firma de ejemplares y encuentro con lectores',
  };

  const original = generateValidated(base, 'descripción: original');
  const changed = generateValidated(changedDescription, 'descripción: mutación');

  assert.notEqual(
    JSON.parse(original.jsonLd).description,
    JSON.parse(changed.jsonLd).description,
    'El contenido descriptivo debe cambiar realmente',
  );
  assert.equal(
    uidOf(original.ics),
    uidOf(changed.ics),
    'Editar la descripción no debe crear otra identidad ICS',
  );
  assert.equal(
    original.filename,
    changed.filename,
    'Editar la descripción no debe cambiar el filename',
  );
});
