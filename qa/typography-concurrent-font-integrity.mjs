import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';

const ROOT = process.cwd();
const CSS = fs.readFileSync(path.join(ROOT, 'assets/v1-fonts.css'), 'utf8');
const BASE = process.env.QA_BASE_URL || process.env.BASE_URL || 'http://127.0.0.1:8000';
const files = [...new Set([...CSS.matchAll(/url\(['\"]?([^)'\"]+\.woff2)['\"]?\)/g)].map(m => m[1]))];
assert(files.length >= 8, `v1-fonts.css: inventario WOFF2 inesperadamente pequeño: ${files.length}`);

async function download(file) {
  const url = new URL(file, new URL('/assets/v1-fonts.css', BASE));
  const response = await fetch(url, { signal: AbortSignal.timeout(15000) });
  assert.equal(response.status, 200, `${url.pathname}: HTTP ${response.status}`);
  const bytes = Buffer.from(await response.arrayBuffer());
  assert(bytes.length > 100, `${url.pathname}: fuente vacía o truncada (${bytes.length} bytes)`);
  assert.equal(bytes.toString('ascii', 0, 4), 'wOF2', `${url.pathname}: firma WOFF2 incorrecta`);
  return createHash('sha256').update(bytes).digest('hex');
}

const requests = files.flatMap(file => Array.from({ length: 4 }, () => ({ file })));
const results = await Promise.all(requests.map(async ({ file }) => ({ file, hash: await download(file) })));
for (const file of files) {
  const hashes = new Set(results.filter(r => r.file === file).map(r => r.hash));
  assert.equal(hashes.size, 1, `${file}: respuestas binarias distintas bajo concurrencia`);
}
console.log(`OK: ${files.length} fuentes WOFF2, ${requests.length} peticiones concurrentes`);