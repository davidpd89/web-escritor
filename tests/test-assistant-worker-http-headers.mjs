import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const source = await fs.readFile(new URL('../cloudflare-worker-assistant.js', import.meta.url), 'utf8');
const { default: worker } = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
const base = 'https://davidportodiaz.com';
const allowed = { Origin: base };
const foreign = { Origin: 'https://evil.example' };
const env = { ASSISTANT_ENABLED: 'false' };

const cases = [
  [new Request(base + '/api/assistant/config', { headers: allowed }), 200],
  [new Request(base + '/api/assistant/config', { headers: foreign }), 403],
  [new Request(base + '/api/assistant', { method: 'GET', headers: allowed }), 405],
  [new Request(base + '/api/assistant', { method: 'POST', headers: allowed, body: '{}' }), 503],
  [new Request(base + '/api/assistant/no-existe', { headers: allowed }), 404],
];
for (const [request, status] of cases) {
  const response = await worker.fetch(request, env);
  assert.equal(response.status, status, request.url);
  assert.equal(response.headers.get('cache-control'), 'no-store', request.url);
  assert.equal(response.headers.get('x-content-type-options'), 'nosniff', request.url);
  assert.match(response.headers.get('content-type') || '', /application\/json/);
  assert.doesNotMatch(await response.text(), /secret-key|stack trace|Error:/i);
}
const preflight = await worker.fetch(new Request(base + '/api/assistant', { method: 'OPTIONS', headers: allowed }), env);
assert.equal(preflight.status, 204);
assert.equal(preflight.headers.get('access-control-allow-origin'), base);
assert.match(preflight.headers.get('access-control-allow-methods') || '', /POST/);
const denied = await worker.fetch(new Request(base + '/api/assistant', { method: 'OPTIONS', headers: foreign }), env);
assert.equal(denied.status, 403);
assert.equal(denied.headers.get('access-control-allow-origin'), null);
console.log('assistant-worker-http-headers: OK');
