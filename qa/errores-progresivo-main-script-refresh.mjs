import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createWorker } from './errores-progresivo-sw-fixture.mjs';

const path = '/script.js';
const published = readFileSync(new URL('../script.js', import.meta.url), 'utf8');
assert.ok(published.length > 100, `${path}: no se ha leído el script publicado`);

let version = published;
const worker = createWorker(async () => new Response(version, {
  status: 200,
  headers: { 'Content-Type': 'text/javascript' }
}));
const request = worker.request(path, { destination: 'script' });

const first = await worker.fetch(request);
assert.equal(await first.response.text(), published, `${path}: primera descarga incorrecta`);

version = published + '\n/* actualización de despliegue */\n';
const second = await worker.fetch(request);
assert.equal(await second.response.text(), version, `${path}: se entregó JavaScript antiguo pese a existir una versión nueva en red`);

worker.setNetwork(async () => { throw new TypeError('Failed to fetch'); });
const offline = await worker.fetch(request);
assert.equal(offline.response.status, 200, `${path}: no se recuperó el script almacenado`);
assert.equal(await offline.response.text(), version, `${path}: la caché conserva una versión anterior al último despliegue`);
console.log('PASS: script.js usa la última versión obtenida de la red');