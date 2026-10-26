import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createWorker } from './errores-progresivo-sw-fixture.mjs';

const path = '/script.js';
const source = readFileSync(new URL('../script.js', import.meta.url), 'utf8');
const worker = createWorker(async () => new Response(source, {
  status: 200,
  headers: { 'Content-Type': 'text/javascript' }
}));
const request = worker.request(path, { destination: 'script' });

const initial = await worker.fetch(request);
assert.equal(initial.response.status, 200, `${path}: no se pudo establecer la copia inicial`);

worker.setNetwork(async () => new Response('Internal Server Error', {
  status: 500,
  headers: { 'Content-Type': 'text/plain' }
}));
const error = await worker.fetch(request);
assert.equal(error.response.status, 500, `${path}: el service worker ha ocultado el error HTTP 500`);

worker.setNetwork(async () => { throw new TypeError('Failed to fetch'); });
const recovered = await worker.fetch(request);
assert.equal(recovered.response.status, 200, `${path}: la respuesta 500 ha invalidado el recurso recuperable`);
assert.equal(await recovered.response.text(), source, `${path}: no se conserva el JavaScript válido anterior`);
console.log('PASS: error 500 no contamina la caché del script principal');