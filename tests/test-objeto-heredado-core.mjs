import assert from 'node:assert/strict';
import { createEmptyRecord, normalizeRecord, parseRecord, serializeRecord, suggestedFilename } from '../assets/objeto-heredado-core.js';

const empty = createEmptyRecord();
assert.equal(empty.schema_version, 1);

const record = normalizeRecord({
  schema_version: 1,
  object: { title: '  Reloj   de bolsillo ', marks: 'ABC\r\n123' },
  owners: [{ person: 'María', certainty: 'comprobado', source_ids: [' F01 '] }],
  evidence: [{ id: 'F01', type: 'factura', description: 'Compra', checked_on: '2026-08-18' }],
  open_questions: [' ¿Quién lo reparó? '],
});
assert.equal(record.object.title, 'Reloj de bolsillo');
assert.equal(record.object.marks, 'ABC\n123');
assert.deepEqual(record.owners[0].source_ids, ['F01']);
assert.equal(suggestedFilename(record), 'reloj-de-bolsillo-procedencia.json');

const serialized = serializeRecord(record);
const roundtrip = parseRecord(serialized);
assert.equal(roundtrip.object.title, 'Reloj de bolsillo');
assert.equal(roundtrip.evidence.length, 1);

// Full documentary record: EXPORT -> PARSE must preserve every semantic field,
// row, order and Unicode character. exported_at is transport metadata and is
// compared separately because serializeRecord deliberately refreshes it.
const full = normalizeRecord({
  schema_version: 1,
  object: {
    title: 'Reloj de pared «A Coruña» — ñ',
    type: 'Reloj mecánico',
    materials: 'Madera, latón y vidrio',
    techniques: 'Torneado y grabado',
    dimensions: '62 × 28 × 14 cm',
    marks: 'N.º 1842\nÁÉÍÓÚ · ü · “marca”',
    distinguishing_features: 'Reparación visible en 1978; esfera sustituida.',
    maker: 'Taller García & Hijos',
    date_period: 'ca. 1938–1942',
    current_location: 'Madrid',
    condition_notes: 'Funciona; arañazo largo en lateral derecho.',
  },
  photos: [
    { filename: 'frente-ñ.jpg', view: 'Frente', note: 'Esfera completa' },
    { filename: 'reverso-02.jpg', view: 'Reverso', note: 'Marca del taller — detalle' },
  ],
  owners: [
    { person: 'María Núñez', from: 'ca. 1942', to: '1968', location: 'A Coruña', transfer: 'Compra', certainty: 'comprobado', source_ids: ['F01'] },
    { person: 'José Díaz', from: '1968', to: '2003', location: 'Pontevedra', transfer: 'Herencia familiar', certainty: 'recuerdo', source_ids: ['F02', 'F03'] },
    { person: 'Elena Porto', from: '2003', to: 'actualidad', location: 'Madrid', transfer: 'Regalo', certainty: 'comprobado', source_ids: ['F03'] },
  ],
  evidence: [
    { id: 'F01', type: 'Factura', description: 'Compra por 125 pesetas', location: 'Caja familiar 2', checked_on: '2026-08-18' },
    { id: 'F02', type: 'Entrevista', description: 'Recuerdo oral de la mudanza', location: 'Audio local', checked_on: '2026-08-19' },
    { id: 'F03', type: 'Fotografía', description: 'Reloj en el salón familiar', location: 'Álbum 4', checked_on: '2026-08-20' },
  ],
  oral_history: [
    { speaker: 'Ana Núñez', interview_date: '2026-08-18', summary: '«Sonaba cada media hora», recuerda Ana.', source_ids: ['F02'], certainty: 'recuerdo' },
    { speaker: 'Elena Porto', interview_date: '2026-08-19', summary: 'No sabe quién cambió la esfera; cree que fue en Vigo.', source_ids: ['F03'], certainty: 'hipotesis' },
  ],
  timeline: [
    { from: 'ca. 1942', to: '', event: 'Compra del reloj.', source_ids: ['F01'], certainty: 'comprobado' },
    { from: '1968', to: '', event: 'Pasa a José por herencia.', source_ids: ['F02'], certainty: 'recuerdo' },
    { from: '1978', to: '', event: 'Reparación probable de la maquinaria.', source_ids: ['F02'], certainty: 'hipotesis' },
    { from: '2003', to: 'actualidad', event: 'Traslado a Madrid.', source_ids: ['F03'], certainty: 'comprobado' },
  ],
  conservation: {
    observed_on: '2026-08-21',
    risks: 'Humedad y exposición solar directa.',
    changes_observed: 'La madera se ha oscurecido ligeramente.',
    next_steps: 'Consultar a un relojero conservador; no pulir el latón.',
  },
  open_questions: ['¿Quién fabricó la esfera actual?', '¿Existe una foto anterior a 1960?', '¿Qué significa la marca «GN-42»?'],
});

const fullSerialized = serializeRecord(full);
const fullParsed = parseRecord(fullSerialized);
const semantic = ({ exported_at, ...rest }) => rest;
assert.deepEqual(semantic(fullParsed), semantic(full));
assert.match(fullParsed.exported_at, /^\d{4}-\d{2}-\d{2}T/);
assert.equal(fullParsed.photos.length, 2);
assert.equal(fullParsed.owners.length, 3);
assert.equal(fullParsed.evidence.length, 3);
assert.equal(fullParsed.oral_history.length, 2);
assert.equal(fullParsed.timeline.length, 4);
assert.equal(fullParsed.open_questions.length, 3);

assert.throws(() => parseRecord('{bad'), /JSON válido/);
assert.throws(() => parseRecord(JSON.stringify({ schema_version: 99 })), /no compatible/);
assert.throws(() => parseRecord(JSON.stringify({ schema_version: 1, photos: 'no-array' })), /debe ser una lista/);
assert.throws(() => parseRecord(JSON.stringify({ schema_version: 1, object: [] })), /formato esperado/);

// Unknown keys and hostile-looking text remain data; they never become code.
const hostile = parseRecord(JSON.stringify({
  schema_version: 1,
  unknown: '<script>alert(1)</script>',
  object: { title: '<img src=x onerror=alert(1)>', marks: '"><svg onload=alert(1)>' },
}));
assert.equal(hostile.object.title, '<img src=x onerror=alert(1)>');
assert.equal(hostile.object.marks, '"><svg onload=alert(1)>');
assert.equal('unknown' in hostile, false);

console.log('tests/test-objeto-heredado-core: OK');