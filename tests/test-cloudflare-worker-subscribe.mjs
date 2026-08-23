// Contract test for cloudflare-worker-subscribe.js.
//
// This does NOT deploy or call the real Cloudflare Worker — it imports the
// module's `fetch` handler directly (Cloudflare Workers use the same
// Request/Response/fetch globals Node provides) and exercises it in-process,
// with global fetch mocked so no real network call to Brevo happens.
//
// What this guards against: the client input contract must stay minimal
// ({ email, source, result? } only). If someone reintroduces reading
// listIds/attributes/updateEnabled from the client body, or removes the
// source whitelist, this test should catch it.

import assert from 'node:assert/strict';
import worker from '../cloudflare-worker-subscribe.js';

const ALLOWED_ORIGIN = 'https://davidportodiaz.com';

function makeEnv(overrides = {}) {
  return { BREVO_API_KEY: 'test-api-key', BREVO_LIST_ID: '3', ...overrides };
}

function makeRequest(body, { method = 'POST', origin = ALLOWED_ORIGIN, headers = {} } = {}) {
  const init = {
    method,
    headers: { Origin: origin, 'Content-Type': 'application/json', ...headers },
  };
  if (body !== undefined && method !== 'OPTIONS' && method !== 'GET') {
    init.body = typeof body === 'string' ? body : JSON.stringify(body);
  }
  return new Request('https://subscribe.example.workers.dev/', init);
}

// Capture whatever the Worker would have sent to Brevo, without hitting the
// network. Restored after each call site below via try/finally.
function withMockedBrevoFetch(fakeStatus, fakeBody, fn) {
  const calls = [];
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url, init) => {
    calls.push({ url, init });
    return new Response(JSON.stringify(fakeBody ?? {}), {
      status: fakeStatus ?? 201,
      headers: { 'Content-Type': 'application/json' },
    });
  };
  return Promise.resolve(fn(calls)).finally(() => {
    globalThis.fetch = originalFetch;
  });
}

async function run() {
  // OPTIONS preflight
  {
    const res = await worker.fetch(makeRequest(undefined, { method: 'OPTIONS' }), makeEnv());
    assert.equal(res.status, 204);
    assert.equal(res.headers.get('Access-Control-Allow-Origin'), ALLOWED_ORIGIN);
  }

  // Wrong method
  {
    const res = await worker.fetch(makeRequest(undefined, { method: 'GET' }), makeEnv());
    assert.equal(res.status, 405);
  }

  // Wrong origin
  {
    const res = await worker.fetch(
      makeRequest({ email: 'a@b.com', source: 'home' }, { origin: 'https://evil.example.com' }),
      makeEnv()
    );
    assert.equal(res.status, 403);
  }

  // Missing email
  {
    const res = await worker.fetch(makeRequest({ source: 'home' }), makeEnv());
    assert.equal(res.status, 400);
  }

  // Invalid email format
  {
    const res = await worker.fetch(makeRequest({ email: 'not-an-email', source: 'home' }), makeEnv());
    assert.equal(res.status, 400);
  }

  // Missing source
  {
    const res = await worker.fetch(makeRequest({ email: 'a@b.com' }), makeEnv());
    assert.equal(res.status, 400);
  }

  // Unknown / not-whitelisted source is rejected
  {
    const res = await worker.fetch(makeRequest({ email: 'a@b.com', source: 'not-a-real-source' }), makeEnv());
    assert.equal(res.status, 400);
  }

  // BREVO_LIST_ID missing server-side -> 500, never falls back to a client value
  {
    const res = await withMockedBrevoFetch(201, {}, () =>
      worker.fetch(makeRequest({ email: 'a@b.com', source: 'home' }), makeEnv({ BREVO_LIST_ID: undefined }))
    );
    assert.equal(res.status, 500);
    const body = await res.json();
    assert.equal(body.ok, false);
  }

  // BREVO_LIST_ID present but not a positive integer -> 500, not silently NaN
  {
    const res = await withMockedBrevoFetch(201, {}, () =>
      worker.fetch(makeRequest({ email: 'a@b.com', source: 'home' }), makeEnv({ BREVO_LIST_ID: 'not-a-number' }))
    );
    assert.equal(res.status, 500);
  }

  // BREVO_API_KEY missing server-side -> 500, explicit check (point 22)
  {
    const res = await withMockedBrevoFetch(201, {}, () =>
      worker.fetch(makeRequest({ email: 'a@b.com', source: 'home' }), makeEnv({ BREVO_API_KEY: undefined }))
    );
    assert.equal(res.status, 500);
  }

  // Success response body is minimal and does not leak Brevo's raw contact
  // payload (id, createdAt, etc.) to the client.
  {
    const res = await withMockedBrevoFetch(201, { id: 42, createdAt: '2026-08-20T00:00:00Z' }, () =>
      worker.fetch(makeRequest({ email: 'reader2@example.com', source: 'home' }), makeEnv())
    );
    assert.equal(res.status, 201);
    const body = await res.json();
    assert.deepEqual(body, { ok: true });
  }

  // Duplicate contact: Brevo's actual error text is never forwarded to the
  // client, only a clean structured flag script.js can check directly.
  {
    const res = await withMockedBrevoFetch(400, { code: 'duplicate_parameter', message: 'Contact already exist' }, () =>
      worker.fetch(makeRequest({ email: 'dupe@example.com', source: 'home' }), makeEnv())
    );
    assert.equal(res.status, 400);
    const body = await res.json();
    assert.deepEqual(body, { ok: false, duplicate: true });
  }

  // Any other Brevo failure (e.g. auth/rate-limit/internal error): the raw
  // Brevo body must never reach the client, and the client-visible message
  // must not contain anything from it.
  {
    const res = await withMockedBrevoFetch(401, { code: 'unauthorized', message: 'Key not found: xkeysib-SECRETVALUE' }, () =>
      worker.fetch(makeRequest({ email: 'reader3@example.com', source: 'home' }), makeEnv())
    );
    assert.equal(res.status, 502);
    const body = await res.json();
    assert.equal(body.ok, false);
    const bodyText = JSON.stringify(body);
    assert.ok(!bodyText.includes('SECRETVALUE'), 'Brevo error detail must not leak to the client');
    assert.ok(!bodyText.includes('unauthorized'), 'Brevo error code must not leak to the client');
  }

  // Valid request: listIds comes from env, not from the client, even when
  // the client tries to smuggle its own listIds/attributes/updateEnabled.
  {
    const calls = [];
    const res = await withMockedBrevoFetch(201, { id: 1 }, async (capturedCalls) => {
      const r = await worker.fetch(
        makeRequest({
          email: 'reader@example.com',
          source: 'home',
          // Attempted contract violation: none of this should reach Brevo.
          listIds: [999],
          attributes: { SOURCE: 'attacker-controlled', ADMIN: true },
          updateEnabled: false,
        }),
        makeEnv()
      );
      calls.push(...capturedCalls);
      return r;
    });
    assert.equal(res.status, 201);
    assert.equal(calls.length, 1);
    const forwarded = JSON.parse(calls[0].init.body);
    assert.equal(forwarded.email, 'reader@example.com');
    assert.deepEqual(forwarded.listIds, [3]); // from env.BREVO_LIST_ID, not the client's [999]
    assert.deepEqual(forwarded.attributes, { SOURCE: 'home' }); // server-derived, not attacker-controlled
    assert.equal(forwarded.updateEnabled, true); // hardcoded server-side, not the client's false
  }

  // Quiz source: a valid result is included as the NOVERIS attribute.
  {
    const calls = [];
    await withMockedBrevoFetch(201, { id: 1 }, async (capturedCalls) => {
      await worker.fetch(makeRequest({ email: 'quiz@example.com', source: 'quiz', result: 'sabio' }), makeEnv());
      calls.push(...capturedCalls);
    });
    const forwarded = JSON.parse(calls[0].init.body);
    assert.deepEqual(forwarded.attributes, { SOURCE: 'quiz-noveris', NOVERIS: 'sabio' });
  }

  // Quiz source with an out-of-enum result: dropped, not forwarded as-is.
  {
    const calls = [];
    await withMockedBrevoFetch(201, { id: 1 }, async (capturedCalls) => {
      await worker.fetch(
        makeRequest({ email: 'quiz2@example.com', source: 'quiz', result: '<script>alert(1)</script>' }),
        makeEnv()
      );
      calls.push(...capturedCalls);
    });
    const forwarded = JSON.parse(calls[0].init.body);
    assert.deepEqual(forwarded.attributes, { SOURCE: 'quiz-noveris' });
  }

  // Non-quiz source: result is ignored even if present.
  {
    const calls = [];
    await withMockedBrevoFetch(201, { id: 1 }, async (capturedCalls) => {
      await worker.fetch(makeRequest({ email: 'pop@example.com', source: 'popup', result: 'sabio' }), makeEnv());
      calls.push(...capturedCalls);
    });
    const forwarded = JSON.parse(calls[0].init.body);
    assert.deepEqual(forwarded.attributes, { SOURCE: 'popup' });
  }

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
    assert.deepEqual(forwarded.listIds, [7], 'lectores-beta debe usar BREVO_BETA_LIST_ID, no BREVO_LIST_ID');
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
    assert.deepEqual(forwarded.listIds, [3], 'home debe seguir usando BREVO_LIST_ID');
  }

  console.log('test-cloudflare-worker-subscribe: all assertions passed');
}

await run();
