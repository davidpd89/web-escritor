import assert from 'node:assert/strict';
import { makeCoverFetcher, storeOrigins } from './lib/cover-store-route.mjs';

const reply = (status, type, body = 'x') => ({ ok: status < 400, status, headers: { get: () => type }, arrayBuffer: async () => Buffer.from(body) });
const sleep = async () => {};
// Pages a ratos devuelve un error HTML: se reintenta y la portada acaba sirviéndose.
let calls = 0;
const flaky = makeCoverFetcher({ sleep, fetchImpl: async () => (++calls < 3 ? reply(429, 'text/html') : reply(200, 'image/webp', 'IMG')) });
const ok = await flaky('https://a.example/p/x.webp');
assert.equal(ok.status, 200);
assert.equal(ok.body.toString(), 'IMG');
// Se cachea: la segunda página no vuelve a pedirla.
await flaky('https://a.example/p/x.webp');
assert.equal(calls, 3);
// Un 404 no se reintenta y se informa como fallo (no se esconde).
let hits = 0;
const missing = await makeCoverFetcher({ sleep, fetchImpl: async () => { hits += 1; return reply(404, 'text/html'); } })('https://a.example/p/no.webp');
assert.equal(missing.status, 502);
assert.equal(hits, 1);
// Un fallo persistente agota los intentos y no queda cacheado.
let down = 0;
const broken = makeCoverFetcher({ sleep, attempts: 2, fetchImpl: async () => { down += 1; throw new Error('ECONNRESET'); } });
assert.equal((await broken('https://a.example/p/y.webp')).status, 502);
await broken('https://a.example/p/y.webp');
assert.equal(down, 4);
assert.deepEqual(storeOrigins({ base: 'https://a.example/p', extra: ['https://b.example/q/'] }), ['https://a.example/p/', 'https://b.example/q/']);
console.log('PASS: portadas del almacén servidas en QA con reintentos y caché');
