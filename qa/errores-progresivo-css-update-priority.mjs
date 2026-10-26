import assert from 'node:assert/strict';
import { createWorker } from './errores-progresivo-sw-fixture.mjs';

const path = '/assets/v1-base.css';
let version = 1;
const worker = createWorker(async () => new Response(`body{--qa-version:${version}}`, {
  status: 200,
  headers: { 'Content-Type': 'text/css; charset=utf-8' }
}));
const request = worker.request(path, { destination: 'style' });

const initial = await worker.fetch(request);
assert.equal(await initial.response.text(), 'body{--qa-version:1}', `${path}: versión inicial`);

version = 2;
worker.setPutFailure((name, url) => name === worker.staticCache && url.endsWith(path));
const originalWarn = console.warn;
console.warn = () => {};
let updated;
try {
  updated = await worker.fetch(request);
} finally {
  console.warn = originalWarn;
}
assert.equal(updated.response.status, 200, `${path}: la escritura fallida no debe convertir HTTP 200 en error`);
assert.equal(await updated.response.text(), 'body{--qa-version:2}', `${path}: se entregó CSS obsoleto pese a estar disponible la versión nueva`);

const cached = await (await worker.caches.open(worker.staticCache)).match(request);
assert(cached, `${path}: desapareció la copia anterior`);
assert.equal(await cached.text(), 'body{--qa-version:1}', `${path}: la escritura fallida alteró la copia existente`);
console.log('PASS CSS network priority');
