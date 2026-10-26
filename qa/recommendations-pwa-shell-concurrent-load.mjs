import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';

const BASE = process.env.RECOMMENDATIONS_BASE_URL || 'http://127.0.0.1:4173';
const source = await readFile('service-worker.js', 'utf8');
const shellBlock = source.match(/const APP_SHELL = \[([\s\S]*?)\];/);
assert(shellBlock, 'service-worker.js: no se encuentra APP_SHELL');
const shell = [...shellBlock[1].matchAll(/["'](\/[^"']+)["']/g)].map(m => m[1]);
assert(shell.includes('/offline.html'), 'service-worker.js: falta offline.html');
assert(shell.includes('/manifest.json'), 'service-worker.js: falta manifest.json');

const paths = [...new Set(['/service-worker.js', ...shell, '/recomendaciones/'])];

async function read(path) {
  const response = await fetch(new URL(path, BASE), { signal: AbortSignal.timeout(15000) });
  assert.equal(response.status, 200, `${path}: HTTP ${response.status}`);
  const bytes = Buffer.from(await response.arrayBuffer());
  assert(bytes.length > 0, `${path}: respuesta vacía`);
  if (path.endsWith('.html') || path.endsWith('/')) {
    assert.match(bytes.toString('utf8'), /<!doctype html|<html\b/i, `${path}: no contiene documento HTML`);
    assert.match(bytes.toString('utf8'), /<\/html\s*>/i, `${path}: HTML incompleto`);
  }
  if (path.endsWith('.js')) assert.match(bytes.toString('utf8'), /addEventListener/, `${path}: script incompleto`);
  if (path.endsWith('.json')) JSON.parse(bytes.toString('utf8'));
  return createHash('sha256').update(bytes).digest('hex');
}

const baseline = new Map();
for (const path of paths) baseline.set(path, await read(path));
const requests = Array.from({ length: 8 }, () => paths).flat();
const results = await Promise.all(requests.map(read));
results.forEach((hash, i) => assert.equal(hash, baseline.get(requests[i]), `${requests[i]}: respuesta alterada bajo carga`));
console.log(`OK: ${results.length} solicitudes concurrentes a ${paths.length} recursos PWA`);
