import assert from 'node:assert/strict';
import { createWorker } from '../qa/errores-progresivo-sw-fixture.mjs';
const sw = createWorker(async req => new Response(req.headers.get('Authorization') || 'anonymous'));
const secret = sw.request('/perfil/', {
  mode: 'navigate', headers: { Authorization: 'Bearer QA_SESSION_A' },
});
const first = await sw.fetch(secret);
assert.equal(await first.response.text(), 'Bearer QA_SESSION_A');
assert.equal(await sw.cacheFor(sw.pageCache).match(secret), undefined,
  'An Authorization response must not become an anonymous offline page');
sw.setNetwork(async () => { throw Error('offline'); });
const anonymous = await sw.fetch(sw.request('/perfil/', { mode: 'navigate' }));
assert.notEqual(await anonymous.response.text(), 'Bearer QA_SESSION_A');
console.log('PASS authorization cache isolation');
