import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';

const BASE = process.env.RECOMMENDATIONS_BASE_URL || 'http://127.0.0.1:4173';
const pageURL = new URL('/recomendaciones/', BASE);
const page = await fetch(pageURL);
assert.equal(page.status, 200, 'Catálogo: respuesta HTTP incorrecta');
const html = await page.text();

const refs = [...html.matchAll(/<(?:script|link)\b[^>]*\b(?:src|href)=["']([^"']+)["'][^>]*>/gi)]
  .map(m => new URL(m[1], pageURL))
  .filter(u => u.origin === pageURL.origin && /\.(?:css|js|mjs)$/i.test(u.pathname));
const urls = [...new Set(refs.map(u => u.href))];
assert(urls.some(u => u.includes('reading-catalogue.js?v=')), 'Catálogo: falta JS versionado');
assert(urls.some(u => u.includes('reading-catalogue.css?v=')), 'Catálogo: falta CSS versionado');

async function load(url) {
  const response = await fetch(url, { signal: AbortSignal.timeout(15000) });
  assert.equal(response.status, 200, `${url}: HTTP ${response.status}`);
  const mime = response.headers.get('content-type') || '';
  const extension = new URL(url).pathname;
  if (extension.endsWith('.css')) assert.match(mime, /text\/css/i, `${url}: MIME ${mime}`);
  else assert.match(mime, /javascript|ecmascript/i, `${url}: MIME ${mime}`);
  const bytes = Buffer.from(await response.arrayBuffer());
  assert(bytes.length > 0, `${url}: cuerpo vacío`);
  return createHash('sha256').update(bytes).digest('hex');
}

const expected = new Map();
for (const url of urls) expected.set(url, await load(url));

const burst = Array.from({ length: 3 }, () => urls).flat();
const hashes = await Promise.all(burst.map(load));
for (let i = 0; i < burst.length; i++) {
  assert.equal(hashes[i], expected.get(burst[i]), `${burst[i]}: contenido distinto bajo carga`);
}
console.log(`OK: ${burst.length} solicitudes concurrentes a ${urls.length} recursos CSS/JS`);
