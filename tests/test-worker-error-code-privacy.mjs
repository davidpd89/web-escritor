import assert from 'node:assert/strict';
import worker from '../cloudflare-worker-subscribe.js';

const email = 'privado@example.com';
const env = {
  BREVO_API_KEY: 'test-key',
  BREVO_LIST_ID: '3',
  BREVO_DOI_TEMPLATE_ID: '42',
  BREVO_DOI_REDIRECT_URL: 'https://davidportodiaz.com/gracias-suscripcion/',
  RATE_LIMITER: { async limit() { return { success: true }; } }
};
const originalFetch = globalThis.fetch;
const originalError = console.error;
const logs = [];
try {
  globalThis.fetch = async () => new Response(JSON.stringify({
    code: `invalid_contact_${email}`,
    message: 'Invalid contact'
  }), { status: 400, headers: { 'Content-Type': 'application/json' } });
  console.error = (...args) => logs.push(args.map(String).join(' '));
  const response = await worker.fetch(new Request('https://subscribe.example.workers.dev/', {
    method: 'POST',
    headers: { Origin: 'https://davidportodiaz.com', 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, source: 'home' })
  }), env);
  assert.equal(response.status, 502);
  assert.ok(logs.length > 0, 'Worker: debe conservarse un diagnóstico del error');
  assert.ok(logs.every(line => !line.includes(email)),
    `Worker: el campo code de Brevo expone ${email} en los logs`);
} finally {
  globalThis.fetch = originalFetch;
  console.error = originalError;
}
