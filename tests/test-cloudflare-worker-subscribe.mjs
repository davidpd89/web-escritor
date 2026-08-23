// Contract tests for the newsletter Worker. No real Brevo or Cloudflare calls.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import worker from '../cloudflare-worker-subscribe.js';

const ALLOWED_ORIGIN = 'https://davidportodiaz.com';
const DOI_ENDPOINT = 'https://api.brevo.com/v3/contacts/doubleOptinConfirmation';
const REDIRECT_URL = 'https://davidportodiaz.com/gracias-suscripcion/';

function makeRateLimiter({ success = true, throwError = null, result = null } = {}) {
  const calls = [];
  return {
    calls,
    async limit(input) {
      calls.push(input);
      if (throwError) throw throwError;
      return result ?? { success };
    },
  };
}

function makeEnv(overrides = {}) {
  return {
    BREVO_API_KEY: 'test-api-key',
    BREVO_LIST_ID: '3',
    BREVO_DOI_TEMPLATE_ID: '42',
    BREVO_DOI_REDIRECT_URL: REDIRECT_URL,
    RATE_LIMITER: makeRateLimiter(),
    ...overrides,
  };
}

function makeRequest(body, { method = 'POST', origin = ALLOWED_ORIGIN } = {}) {
  const init = { method, headers: { Origin: origin, 'Content-Type': 'application/json' } };
  if (body !== undefined && method !== 'OPTIONS' && method !== 'GET') {
    init.body = typeof body === 'string' ? body : JSON.stringify(body);
  }
  return new Request('https://subscribe.example.workers.dev/', init);
}

function withMockedBrevoFetch(fakeStatus, fakeBody, fn, { throwError = null } = {}) {
  const calls = [];
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url, init) => {
    calls.push({ url, init });
    if (throwError) throw throwError;
    const body = fakeStatus === 204 ? null : JSON.stringify(fakeBody ?? {});
    return new Response(body, { status: fakeStatus, headers: { 'Content-Type': 'application/json' } });
  };
  return Promise.resolve(fn(calls)).finally(() => { globalThis.fetch = originalFetch; });
}

async function run() {
  const source = await fs.readFile(new URL('../cloudflare-worker-subscribe.js', import.meta.url), 'utf8');
  assert.ok(source.includes('/v3/contacts/doubleOptinConfirmation'));
  assert.ok(!source.includes('fetch("https://api.brevo.com/v3/contacts"'));

  let res = await worker.fetch(makeRequest(undefined, { method: 'OPTIONS' }), makeEnv());
  assert.equal(res.status, 204);
  assert.equal(res.headers.get('Access-Control-Allow-Origin'), ALLOWED_ORIGIN);
  assert.equal(res.headers.get('Vary'), 'Origin');

  res = await worker.fetch(makeRequest(undefined, { method: 'OPTIONS', origin: 'https://evil.example' }), makeEnv());
  assert.equal(res.status, 204);
  assert.equal(res.headers.get('Access-Control-Allow-Origin'), null);

  res = await worker.fetch(makeRequest(undefined, { method: 'GET' }), makeEnv());
  assert.equal(res.status, 405);
  res = await worker.fetch(makeRequest({ email: 'a@b.com', source: 'home' }, { origin: 'https://evil.example' }), makeEnv());
  assert.equal(res.status, 403);

  res = await worker.fetch(makeRequest('{not json'), makeEnv());
  assert.equal(res.status, 400);
  for (const invalid of [
    { source: 'home' },
    { email: 'not-an-email', source: 'home' },
    { email: 'a@b.com', source: 'unknown-source' },
  ]) {
    res = await withMockedBrevoFetch(201, {}, calls => worker.fetch(makeRequest(invalid), makeEnv()).then(r => {
      assert.equal(calls.length, 0); return r;
    }));
    assert.equal(res.status, 400);
  }

  for (const [name, value] of [
    ['BREVO_API_KEY', undefined],
    ['BREVO_LIST_ID', undefined], ['BREVO_LIST_ID', 'bad'],
    ['BREVO_DOI_TEMPLATE_ID', undefined], ['BREVO_DOI_TEMPLATE_ID', '0'],
    ['BREVO_DOI_REDIRECT_URL', undefined],
    ['BREVO_DOI_REDIRECT_URL', 'http://davidportodiaz.com/gracias-suscripcion/'],
    ['BREVO_DOI_REDIRECT_URL', 'not-a-url'],
  ]) {
    res = await withMockedBrevoFetch(201, {}, calls => worker.fetch(
      makeRequest({ email: 'config@example.com', source: 'home' }), makeEnv({ [name]: value })
    ).then(r => { assert.equal(calls.length, 0); return r; }));
    assert.equal(res.status, 500, `${name}=${String(value)}`);
  }

  const limiter = makeRateLimiter();
  res = await withMockedBrevoFetch(201, {}, async calls => {
    const response = await worker.fetch(makeRequest({
      email: ' Reader@Example.com ', source: 'home', listIds: [999], includeListIds: [999],
      templateId: 999, redirectionUrl: 'https://evil.example/',
      attributes: { SOURCE: 'attacker', ADMIN: true }, updateEnabled: true,
    }), makeEnv({ RATE_LIMITER: limiter }));
    assert.equal(calls.length, 1);
    assert.equal(calls[0].url, DOI_ENDPOINT);
    const forwarded = JSON.parse(calls[0].init.body);
    assert.deepEqual(forwarded, {
      email: 'Reader@Example.com', includeListIds: [3], redirectionUrl: REDIRECT_URL,
      templateId: 42, attributes: { SOURCE: 'home' },
    });
    assert.equal('listIds' in forwarded, false);
    assert.equal('updateEnabled' in forwarded, false);
    return response;
  });
  assert.equal(res.status, 201);
  assert.deepEqual(await res.json(), { ok: true, state: 'pending_confirmation' });
  assert.equal(limiter.calls.length, 1);
  assert.match(limiter.calls[0].key, /^newsletter:[a-f0-9]{64}$/);
  assert.ok(!limiter.calls[0].key.includes('Reader@Example.com'));

  await withMockedBrevoFetch(201, {}, async calls => {
    await worker.fetch(makeRequest({ email: 'quiz@example.com', source: 'quiz', result: 'sabio' }), makeEnv());
    assert.deepEqual(JSON.parse(calls[0].init.body).attributes, { SOURCE: 'quiz-noveris', NOVERIS: 'sabio' });
  });
  await withMockedBrevoFetch(201, {}, async calls => {
    await worker.fetch(makeRequest({ email: 'quiz2@example.com', source: 'quiz', result: '<script>' }), makeEnv());
    assert.deepEqual(JSON.parse(calls[0].init.body).attributes, { SOURCE: 'quiz-noveris' });
  });

  const hpLimiter = makeRateLimiter({ success: false });
  res = await withMockedBrevoFetch(201, {}, async calls => {
    const response = await worker.fetch(makeRequest({ email: 'bot@example.com', source: 'home', website: 'spam' }), makeEnv({ RATE_LIMITER: hpLimiter }));
    assert.equal(calls.length, 0); return response;
  });
  assert.equal(hpLimiter.calls.length, 0);
  assert.equal(res.status, 201);
  assert.deepEqual(await res.json(), { ok: true, state: 'pending_confirmation' });

  const blockedLimiter = makeRateLimiter({ success: false });
  res = await withMockedBrevoFetch(201, {}, async calls => {
    const response = await worker.fetch(makeRequest({ email: 'limited@example.com', source: 'home' }), makeEnv({ RATE_LIMITER: blockedLimiter }));
    assert.equal(calls.length, 0); return response;
  });
  assert.equal(res.status, 429);

  for (const rateOverride of [undefined, {}, makeRateLimiter({ throwError: new Error('binding unavailable') }), makeRateLimiter({ result: {} })]) {
    res = await withMockedBrevoFetch(201, {}, calls => worker.fetch(
      makeRequest({ email: 'degraded@example.com', source: 'home' }), makeEnv({ RATE_LIMITER: rateOverride })
    ).then(r => { assert.equal(calls.length, 1); return r; }));
    assert.equal(res.status, 201);
  }

  res = await withMockedBrevoFetch(401, { code: 'unauthorized', message: 'xkeysib-SECRETVALUE' }, () =>
    worker.fetch(makeRequest({ email: 'reader@example.com', source: 'home' }), makeEnv())
  );
  assert.equal(res.status, 502);
  const safeError = JSON.stringify(await res.json());
  assert.ok(!safeError.includes('SECRETVALUE'));
  assert.ok(!safeError.includes('unauthorized'));

  res = await withMockedBrevoFetch(201, {}, () => worker.fetch(
    makeRequest({ email: 'reader@example.com', source: 'home' }), makeEnv()
  ), { throwError: new Error('network down') });
  assert.equal(res.status, 502);

  res = await withMockedBrevoFetch(204, undefined, () => worker.fetch(
    makeRequest({ email: 'reader@example.com', source: 'home' }), makeEnv()
  ));
  assert.equal(res.status, 502);

  // Lectores Beta (N.1): usa BREVO_BETA_LIST_ID, no BREVO_LIST_ID -- listas
  // separadas para no mezclar consentimiento/proposito.
  {
    const calls = [];
    await withMockedBrevoFetch(201, { id: 1 }, async (capturedCalls) => {
      await worker.fetch(
        makeRequest({ email: 'beta@example.com', source: 'lectores-beta' }),
        makeEnv({ BREVO_LIST_ID: '3', BREVO_BETA_LIST_ID: '7' }),
      );
      calls.push(...capturedCalls);
    });
    const forwarded = JSON.parse(calls[0].init.body);
    assert.deepEqual(forwarded.includeListIds, [7], 'lectores-beta debe usar BREVO_BETA_LIST_ID, no BREVO_LIST_ID');
    assert.deepEqual(forwarded.attributes, { SOURCE: 'lectores-beta' });
  }

  // Lectores Beta sin BREVO_BETA_LIST_ID configurado -> 500, NUNCA cae a la
  // lista general (fallar cerrado, no mezclar listas).
  {
    const res = await withMockedBrevoFetch(201, {}, () =>
      worker.fetch(
        makeRequest({ email: 'beta2@example.com', source: 'lectores-beta' }),
        makeEnv({ BREVO_LIST_ID: '3', BREVO_BETA_LIST_ID: undefined }),
      )
    );
    assert.equal(res.status, 500);
  }

  // Las fuentes generales siguen usando BREVO_LIST_ID sin verse afectadas
  // por la nueva variable BREVO_BETA_LIST_ID.
  {
    const calls = [];
    await withMockedBrevoFetch(201, { id: 1 }, async (capturedCalls) => {
      await worker.fetch(
        makeRequest({ email: 'general@example.com', source: 'home' }),
        makeEnv({ BREVO_LIST_ID: '3', BREVO_BETA_LIST_ID: '7' }),
      );
      calls.push(...capturedCalls);
    });
    const forwarded = JSON.parse(calls[0].init.body);
    assert.deepEqual(forwarded.includeListIds, [3], 'home debe seguir usando BREVO_LIST_ID');
  }

  console.log('test-cloudflare-worker-subscribe: all assertions passed');
}
await run();
