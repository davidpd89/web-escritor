import assert from 'node:assert/strict';
import { createWorker } from '../qa/errores-progresivo-sw-fixture.mjs';
const sw = createWorker(async () => new Response('public', { status: 200 }));
for (const path of ['/api', '/api/config?edition=1', '/api/v2/session']) {
  const result = await sw.fetch(sw.request(path));
  assert.equal(result.intercepted, false, `${path} must bypass the worker`);
}
assert.deepEqual(sw.entries(sw.pageCache), [], 'API data reached PAGE_CACHE');
const normal = await sw.fetch(sw.request('/apiary/index.json'));
assert.equal(normal.intercepted, true, 'API prefix check swallowed /apiary');
assert.equal(normal.response.status, 200);
assert.equal(sw.entries(sw.pageCache).length, 1);
console.log('PASS SW API prefix boundaries');
