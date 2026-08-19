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

assert.throws(() => parseRecord('{bad'), /JSON válido/);
assert.throws(() => parseRecord(JSON.stringify({ schema_version: 99 })), /no compatible/);

console.log('tests/test-objeto-heredado-core: OK');
