import assert from 'node:assert/strict';
import { crc32, strToU8, zipStoreSync } from '../assets/zip-store-lite.js';

// Standard CRC-32 check value for the ASCII string "123456789".
assert.equal(crc32(strToU8('123456789')), 0xcbf43926);
assert.equal(crc32(strToU8('')), 0);

const files = {
  'README.txt': strToU8('hola mundo\n'),
  'datos/autor.json': strToU8(JSON.stringify({ name: 'José María Ñoño' }, null, 2) + '\n'),
};
const zip = zipStoreSync(files, { mtime: new Date('2026-01-01T00:00:00') });

assert.ok(zip instanceof Uint8Array);
// Local file header signature at the very start.
assert.equal(zip[0], 0x50); assert.equal(zip[1], 0x4b); assert.equal(zip[2], 0x03); assert.equal(zip[3], 0x04);
// End-of-central-directory signature (PK\x05\x06) must appear near the end.
const tail = Array.from(zip.slice(-22));
assert.deepEqual(tail.slice(0, 4), [0x50, 0x4b, 0x05, 0x06]);

// Manually walk the local file headers and confirm both entries round-trip
// byte-for-byte (name + content), independent of the writer's own logic.
function readLocalEntries(bytes) {
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const entries = [];
  let offset = 0;
  while (offset < bytes.length) {
    const sig = view.getUint32(offset, true);
    if (sig !== 0x04034b50) break;
    const compSize = view.getUint32(offset + 18, true);
    const nameLen = view.getUint16(offset + 26, true);
    const extraLen = view.getUint16(offset + 28, true);
    const nameStart = offset + 30;
    const dataStart = nameStart + nameLen + extraLen;
    const name = new TextDecoder().decode(bytes.slice(nameStart, nameStart + nameLen));
    const data = bytes.slice(dataStart, dataStart + compSize);
    entries.push({ name, data });
    offset = dataStart + compSize;
  }
  return entries;
}

const entries = readLocalEntries(zip);
assert.equal(entries.length, 2);
assert.equal(entries[0].name, 'README.txt');
assert.equal(new TextDecoder().decode(entries[0].data), 'hola mundo\n');
assert.equal(entries[1].name, 'datos/autor.json');
assert.equal(new TextDecoder().decode(entries[1].data), JSON.stringify({ name: 'José María Ñoño' }, null, 2) + '\n');

// Rejects non-Uint8Array input instead of silently producing a broken archive.
assert.throws(() => zipStoreSync({ 'bad.txt': 'not bytes' }), TypeError);

console.log('tests/test-zip-store-lite: OK');
