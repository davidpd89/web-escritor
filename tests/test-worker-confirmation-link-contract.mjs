import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import worker from '../cloudflare-worker-subscribe.js';

const page = await readFile(new URL('../gracias-suscripcion/index.html', import.meta.url), 'utf8');
const canonical = page.match(/<link\s+rel="canonical"\s+href="([^"]+)"/i)?.[1];
assert.ok(canonical, 'gracias-suscripcion/index.html: falta canonical');
const destination = new URL(canonical);
assert.equal(destination.origin, 'https://davidportodiaz.com');
assert.equal(destination.pathname, '/gracias-suscripcion/');
assert.match(page, /<meta\s+name="robots"\s+content="noindex, follow"/i);

const env = {
  BREVO_API_KEY: 'test-key', BREVO_LIST_ID: '3', BREVO_DOI_TEMPLATE_ID: '42',
  BREVO_DOI_REDIRECT_URL: canonical,
  RATE_LIMITER: { async limit() { return { success: true }; } }
};
const originalFetch = globalThis.fetch;
let payload;
try {
  globalThis.fetch = async (url, init) => {
    payload = JSON.parse(init.body);
    return new Response('{}', { status: 201 });
  };
  const response = await worker.fetch(new Request('https://subscribe.example.workers.dev/', {
    method: 'POST',
    headers: { Origin: 'https://davidportodiaz.com', 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: 'reader@example.com', source: 'home' })
  }), env);
  assert.equal(response.status, 201);
  assert.equal(payload.redirectionUrl, canonical,
    'Worker: el destino DOI no coincide con la página publicada');
  assert.equal(new URL(payload.redirectionUrl).origin, destination.origin);
} finally {
  globalThis.fetch = originalFetch;
}
