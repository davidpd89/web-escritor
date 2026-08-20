// Contrato del doc 36: dos generaciones del mismo kit deben producir un ZIP
// identico byte a byte. Antes zipStoreSync usaba new Date() por defecto, asi
// que el mismo contenido salia distinto en cada ejecucion; y dosDateTime leia
// la hora local, asi que ademas dependia de la zona horaria del navegador.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { strToU8, zipStoreSync, ZIP_EPOCH } from '../assets/zip-store-lite.js';

const sha = (bytes) => createHash('sha256').update(Buffer.from(bytes)).digest('hex');

const files = {
  'kit/README.txt': strToU8('Kit de prensa\n'),
  'kit/bio.txt': strToU8('Bio de ejemplo con acentos: ñ á é\n'),
  'kit/manifest.json': strToU8(JSON.stringify({ v: 1 })),
};

// 1. Reproducible entre llamadas
const a = zipStoreSync(files);
const b = zipStoreSync(files);
assert.equal(sha(a), sha(b), 'dos ZIP con el mismo contenido deben tener el mismo SHA-256');

// 2. Reproducible independientemente de la zona horaria del cliente
const original = process.env.TZ;
process.env.TZ = 'America/Los_Angeles';
const west = zipStoreSync(files);
process.env.TZ = 'Asia/Tokyo';
const east = zipStoreSync(files);
process.env.TZ = original;
assert.equal(sha(west), sha(east), 'el ZIP no debe depender de la zona horaria');
assert.equal(sha(west), sha(a), 'el ZIP debe ser el mismo en cualquier zona horaria');

// 3. El epoch por defecto es 1980-01-01, no la hora actual
assert.equal(ZIP_EPOCH.getUTCFullYear(), 1980);
assert.equal(ZIP_EPOCH.getUTCMonth(), 0);
assert.equal(ZIP_EPOCH.getUTCDate(), 1);

// 4. Contenido distinto => ZIP distinto (el test no pasa por ser todo constante)
const other = zipStoreSync({ ...files, 'kit/bio.txt': strToU8('otra bio\n') });
assert.notEqual(sha(other), sha(a), 'contenido distinto debe dar un ZIP distinto');

// 5. Sigue siendo un ZIP valido: firma local y EOCD
assert.equal(a[0], 0x50); assert.equal(a[1], 0x4b);
assert.equal(a[2], 0x03); assert.equal(a[3], 0x04);
const eocd = Buffer.from(a).lastIndexOf(Buffer.from([0x50, 0x4b, 0x05, 0x06]));
assert.ok(eocd > 0, 'debe existir el End Of Central Directory');

console.log('test-zip-store-lite: OK');
