// Helper invoked by tests/test-zip-store-lite-roundtrip.py: builds a fixed
// set of test files (ASCII, unicode content, unicode filename, an empty
// file, a nested path, and a >1KB file) and writes the resulting ZIP to the
// path given as argv[2], so a completely independent parser (Python's
// zipfile) can verify it actually decompresses -- not just that it looks
// like a ZIP (magic bytes) or is reproducible, which is all the existing
// tests/test-zip-store-lite.mjs checks.
import { writeFileSync } from 'node:fs';
import { strToU8, zipStoreSync } from '../../assets/zip-store-lite.js';

const outPath = process.argv[2];
if (!outPath) {
  console.error('usage: node zip-store-lite-roundtrip-gen.mjs <output.zip>');
  process.exit(1);
}

const files = {
  'kit/README.txt': strToU8('Kit de prensa\n'),
  'kit/bio.txt': strToU8('Bio de ejemplo con acentos: ñ á é ü chino 中文 emoji 🎉\n'),
  'kit/manifest.json': strToU8(JSON.stringify({ v: 1, nested: { a: [1, 2, 3] } })),
  'kit/empty.txt': strToU8(''),
  'kit/sub/dir/file.txt': strToU8('archivo en subcarpeta\n'.repeat(50)),
  'kit/assets/foto-José-Ñoño.jpg': strToU8('fake-jpeg-bytes-not-a-real-image'),
};

writeFileSync(outPath, zipStoreSync(files));

// Print the expected content as JSON so the Python side can assert on it
// without duplicating the file list by hand.
const expected = Object.fromEntries(
  Object.entries(files).map(([path, bytes]) => [path, Buffer.from(bytes).toString('utf-8')])
);
console.log(JSON.stringify(expected));
