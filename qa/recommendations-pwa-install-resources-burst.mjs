import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';

const BASE = process.env.RECOMMENDATIONS_BASE_URL || 'http://127.0.0.1:4173';
const root = new URL(BASE);
const html = await (await fetch(new URL('/recomendaciones/', root))).text();
const manifestPath = html.match(/<link\b[^>]*rel=["']manifest["'][^>]*href=["']([^"']+)/i)?.[1];
assert(manifestPath, '/recomendaciones/: falta enlace al manifiesto');

const manifestURL = new URL(manifestPath, root);
const manifestResponse = await fetch(manifestURL);
assert.equal(manifestResponse.status, 200, `${manifestURL}: HTTP incorrecto`);
const manifest = await manifestResponse.json();
assert(Array.isArray(manifest.icons) && manifest.icons.length > 0, 'manifest.json: no hay iconos');

const resources = [manifestURL.href, ...manifest.icons.map(icon => new URL(icon.src, manifestURL).href)];

async function read(url) {
  const response = await fetch(url, { signal: AbortSignal.timeout(15000) });
  assert.equal(response.status, 200, `${url}: HTTP ${response.status}`);
  const bytes = Buffer.from(await response.arrayBuffer());
  assert(bytes.length > 0, `${url}: respuesta vacía`);
  if (url === manifestURL.href) {
    const parsed = JSON.parse(bytes.toString('utf8'));
    assert(parsed.icons?.length > 0, `${url}: manifiesto incompleto`);
  } else {
    assert.equal(bytes.subarray(0, 8).toString('hex'), '89504e470d0a1a0a', `${url}: firma PNG inválida`);
    const icon = manifest.icons.find(i => new URL(i.src, manifestURL).href === url);
    const declared = icon.sizes.match(/^(\d+)x(\d+)$/);
    assert(declared, `${url}: dimensiones no interpretables`);
    assert.equal(bytes.readUInt32BE(16), Number(declared[1]), `${url}: anchura incorrecta`);
    assert.equal(bytes.readUInt32BE(20), Number(declared[2]), `${url}: altura incorrecta`);
  }
  return createHash('sha256').update(bytes).digest('hex');
}

const baseline = new Map();
for (const url of resources) baseline.set(url, await read(url));
const burst = Array.from({ length: 12 }, () => resources).flat();
const results = await Promise.all(burst.map(read));
results.forEach((hash, i) => assert.equal(hash, baseline.get(burst[i]), `${burst[i]}: bytes alterados durante la ráfaga`));
console.log(`OK: ${burst.length} solicitudes concurrentes de manifiesto e iconos`);
