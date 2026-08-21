import fs from 'node:fs/promises';
import assert from 'node:assert/strict';

const source = await fs.readFile(new URL('../cloudflare-worker-subscribe.js', import.meta.url), 'utf8');
const moduleUrl = `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`;
const worker = (await import(moduleUrl)).default;
const ORIGIN = 'https://davidportodiaz.com';
const ENDPOINT = 'https://subscribe.davidpd89.workers.dev';
const ENV = { BREVO_API_KEY: 'qa-secret-never-live', BREVO_LIST_ID: '3' };
const EMAIL = 'qa-newsletter@example.test';

function req(body, { method = 'POST', origin = ORIGIN } = {}) {
  return new Request(ENDPOINT, {
    method,
    headers: { Origin: origin, 'Content-Type': 'application/json' },
    body: method === 'POST' ? JSON.stringify(body) : undefined,
  });
}

async function withFetch(responseFactory, fn) {
  const original = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (url, init = {}) => {
    calls.push({ url: String(url), init });
    return responseFactory(url, init);
  };
  try { return await fn(calls); }
  finally { globalThis.fetch = original; }
}

// CORS / method / origin gates are intrinsic and never call Brevo.
{
  const res = await worker.fetch(req(null, { method: 'OPTIONS' }), ENV);
  assert.equal(res.status, 204);
  assert.equal(res.headers.get('access-control-allow-origin'), ORIGIN);
}
{
  const res = await worker.fetch(new Request(ENDPOINT, { method: 'GET', headers: { Origin: ORIGIN } }), ENV);
  assert.equal(res.status, 405);
}
{
  const res = await worker.fetch(req({ email: EMAIL, source: 'home' }, { origin: 'https://example.test' }), ENV);
  assert.equal(res.status, 403);
}

for (const body of [
  {},
  { email: 'not-an-email', source: 'home' },
  { email: EMAIL, source: 'unknown' },
]) {
  await withFetch(() => { throw new Error('Brevo must not be called for invalid input'); }, async (calls) => {
    const res = await worker.fetch(req(body), ENV);
    assert.equal(res.status, 400);
    assert.equal(calls.length, 0);
  });
}

// Browser-controlled fields beyond {email, source, result?} must be ignored.
await withFetch(async (_url, init) => {
  const brevoBody = JSON.parse(init.body);
  assert.deepEqual(brevoBody, {
    email: EMAIL,
    listIds: [3],
    attributes: { SOURCE: 'home' },
    updateEnabled: true,
  });
  assert.equal(init.headers['api-key'], ENV.BREVO_API_KEY);
  return new Response(JSON.stringify({ id: 1 }), { status: 201, headers: { 'Content-Type': 'application/json' } });
}, async (calls) => {
  const res = await worker.fetch(req({
    email: EMAIL,
    source: 'home',
    consent: true,
    consent_timestamp: '2099-01-01T00:00:00Z',
    listIds: [999],
    attributes: { ADMIN: 'yes' },
    updateEnabled: false,
  }), ENV);
  assert.equal(res.status, 201);
  assert.deepEqual(await res.json(), { ok: true });
  assert.equal(calls.length, 1);
  assert.equal(calls[0].url, 'https://api.brevo.com/v3/contacts');
});

// Quiz result is bounded server-side.
await withFetch(async (_url, init) => {
  assert.deepEqual(JSON.parse(init.body).attributes, { SOURCE: 'quiz-noveris', NOVERIS: 'guardian' });
  return new Response(null, { status: 204 });
}, async () => {
  const res = await worker.fetch(req({ email: EMAIL, source: 'quiz', result: 'guardian' }), ENV);
  assert.equal(res.status, 204);
  assert.equal(await res.text(), '');
});

await withFetch(async (_url, init) => {
  assert.deepEqual(JSON.parse(init.body).attributes, { SOURCE: 'quiz-noveris' });
  return new Response(JSON.stringify({ id: 1 }), { status: 201 });
}, async () => {
  const res = await worker.fetch(req({ email: EMAIL, source: 'quiz', result: '<script>' }), ENV);
  assert.equal(res.status, 201);
});

// Duplicate is the only Brevo 400 exposed as a distinct browser-safe condition.
await withFetch(async () => new Response(JSON.stringify({ message: 'Contact already exists' }), { status: 400 }), async () => {
  const res = await worker.fetch(req({ email: EMAIL, source: 'home' }), ENV);
  assert.equal(res.status, 400);
  assert.deepEqual(await res.json(), { ok: false, duplicate: true });
});

// Other upstream failures are normalized; raw provider detail/API key never leaks.
await withFetch(async () => new Response('secret upstream detail', { status: 500 }), async () => {
  const res = await worker.fetch(req({ email: EMAIL, source: 'home' }), ENV);
  assert.equal(res.status, 502);
  const text = await res.text();
  assert(!text.includes('secret upstream detail'));
  assert(!text.includes(ENV.BREVO_API_KEY));
});

console.log('newsletter Worker contract: PASS');
