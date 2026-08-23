import fs from 'node:fs/promises';
import assert from 'node:assert/strict';

const source = await fs.readFile(new URL('../cloudflare-worker-subscribe.js', import.meta.url), 'utf8');
const moduleUrl = `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`;
const worker = (await import(moduleUrl)).default;
const ORIGIN = 'https://davidportodiaz.com';
const ENDPOINT = 'https://subscribe.davidpd89.workers.dev';
const DOI_ENDPOINT = 'https://api.brevo.com/v3/contacts/doubleOptinConfirmation';
const REDIRECT = 'https://davidportodiaz.com/gracias-suscripcion/';
const EMAIL = 'qa-newsletter@example.test';

function limiter(success = true) {
  return {
    calls: [],
    async limit(arg) {
      this.calls.push(arg);
      return { success };
    },
  };
}

function env(overrides = {}) {
  return {
    BREVO_API_KEY: 'qa-secret-never-live',
    BREVO_LIST_ID: '3',
    BREVO_DOI_TEMPLATE_ID: '42',
    BREVO_DOI_REDIRECT_URL: REDIRECT,
    RATE_LIMITER: limiter(),
    ...overrides,
  };
}

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
  const res = await worker.fetch(req(null, { method: 'OPTIONS' }), env());
  assert.equal(res.status, 204);
  assert.equal(res.headers.get('access-control-allow-origin'), ORIGIN);
  assert.equal(res.headers.get('vary'), 'Origin');
}
{
  const res = await worker.fetch(new Request(ENDPOINT, { method: 'GET', headers: { Origin: ORIGIN } }), env());
  assert.equal(res.status, 405);
}
{
  const res = await worker.fetch(req({ email: EMAIL, source: 'home' }, { origin: 'https://example.test' }), env());
  assert.equal(res.status, 403);
}

for (const body of [
  {},
  { email: 'not-an-email', source: 'home' },
  { email: EMAIL },
  { email: EMAIL, source: 'unknown' },
]) {
  await withFetch(() => { throw new Error('Brevo must not be called for invalid input'); }, async calls => {
    const res = await worker.fetch(req(body), env());
    assert.equal(res.status, 400);
    assert.equal(calls.length, 0);
  });
}

// Server-side DOI fields cannot be overridden by the browser.
await withFetch(async (_url, init) => {
  const payload = JSON.parse(init.body);
  assert.deepEqual(payload, {
    email: EMAIL,
    includeListIds: [3],
    redirectionUrl: REDIRECT,
    templateId: 42,
    attributes: { SOURCE: 'home' },
  });
  assert.equal(init.headers['api-key'], 'qa-secret-never-live');
  return new Response('{}', { status: 201, headers: { 'Content-Type': 'application/json' } });
}, async calls => {
  const res = await worker.fetch(req({
    email: EMAIL,
    source: 'home',
    consent: true,
    listIds: [999],
    includeListIds: [999],
    templateId: 999,
    redirectionUrl: 'https://evil.test/',
    attributes: { ADMIN: 'yes' },
    updateEnabled: false,
  }), env());
  assert.equal(res.status, 201);
  assert.deepEqual(await res.json(), { ok: true, state: 'pending_confirmation' });
  assert.equal(calls.length, 1);
  assert.equal(calls[0].url, DOI_ENDPOINT);
});

// Quiz result remains bounded server-side; non-quiz result is ignored.
await withFetch(async (_url, init) => {
  assert.deepEqual(JSON.parse(init.body).attributes, { SOURCE: 'quiz-noveris', NOVERIS: 'guardian' });
  return new Response('{}', { status: 201 });
}, async () => {
  const res = await worker.fetch(req({ email: EMAIL, source: 'quiz', result: 'guardian' }), env());
  assert.equal(res.status, 201);
});
await withFetch(async (_url, init) => {
  assert.deepEqual(JSON.parse(init.body).attributes, { SOURCE: 'quiz-noveris' });
  return new Response('{}', { status: 201 });
}, async () => {
  const res = await worker.fetch(req({ email: EMAIL, source: 'quiz', result: '<script>' }), env());
  assert.equal(res.status, 201);
});
await withFetch(async (_url, init) => {
  assert.deepEqual(JSON.parse(init.body).attributes, { SOURCE: 'popup' });
  return new Response('{}', { status: 201 });
}, async () => {
  const res = await worker.fetch(req({ email: EMAIL, source: 'popup', result: 'guardian' }), env());
  assert.equal(res.status, 201);
});

// Honeypot and limiter are deterministic and never require real Cloudflare.
{
  const blocked = limiter(false);
  await withFetch(() => { throw new Error('Brevo must not be called while limited'); }, async calls => {
    const res = await worker.fetch(req({ email: EMAIL, source: 'home' }), env({ RATE_LIMITER: blocked }));
    assert.equal(res.status, 429);
    assert.equal(calls.length, 0);
    assert.equal(blocked.calls.length, 1);
  });
}
{
  const blocked = limiter(false);
  await withFetch(() => { throw new Error('Brevo must not be called for honeypot'); }, async calls => {
    const res = await worker.fetch(req({ email: EMAIL, source: 'home', website: 'bot' }), env({ RATE_LIMITER: blocked }));
    assert.equal(res.status, 201);
    assert.deepEqual(await res.json(), { ok: true, state: 'pending_confirmation' });
    assert.equal(calls.length, 0);
    assert.equal(blocked.calls.length, 0);
  });
}

// Missing DOI configuration must fail closed before Brevo.
for (const overrides of [
  { BREVO_DOI_TEMPLATE_ID: undefined },
  { BREVO_DOI_REDIRECT_URL: undefined },
  { BREVO_LIST_ID: undefined },
  { BREVO_API_KEY: undefined },
]) {
  await withFetch(() => { throw new Error('Brevo must not be called with incomplete config'); }, async calls => {
    const res = await worker.fetch(req({ email: EMAIL, source: 'home' }), env(overrides));
    assert.equal(res.status, 500);
    assert.equal(calls.length, 0);
  });
}

// A legacy duplicate response is not confirmation under DOI.
await withFetch(async () => new Response(JSON.stringify({ message: 'Contact already exists', email: EMAIL }), { status: 400 }), async () => {
  const res = await worker.fetch(req({ email: EMAIL, source: 'home' }), env());
  assert.equal(res.status, 502);
  const text = await res.text();
  assert(!text.includes(EMAIL));
  assert(!text.includes('already exists'));
});

// Other upstream failures are normalized; raw provider detail/API key never leaks.
await withFetch(async () => new Response('secret upstream detail', { status: 500 }), async () => {
  const res = await worker.fetch(req({ email: EMAIL, source: 'home' }), env());
  assert.equal(res.status, 502);
  const text = await res.text();
  assert(!text.includes('secret upstream detail'));
  assert(!text.includes('qa-secret-never-live'));
});

console.log('newsletter Worker contract: PASS');
