import assert from 'node:assert/strict';
import worker from '../cloudflare-worker-subscribe.js';

const email = 'lector.privado@example.com';
const env = {
  BREVO_API_KEY: 'test-key',
  BREVO_LIST_ID: '3',
  BREVO_DOI_TEMPLATE_ID: '42',
  BREVO_DOI_REDIRECT_URL: 'https://davidportodiaz.com/gracias-suscripcion/',
  RATE_LIMITER: { async limit() { return { success: true }; } }
};
const request = new Request('https://subscribe.example.workers.dev/', {
  method: 'POST',
  headers: { Origin: 'https://davidportodiaz.com', 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, source: 'home' })
});
const originalFetch = globalThis.fetch;
const originalError = console.error;
const logs = [];
try {
  globalThis.fetch = async () => { throw new Error(`Network failure for ${email}`); };
  console.error = (...args) => logs.push(args.map(String).join(' '));
  const response = await worker.fetch(request, env);
  assert.equal(response.status, 502, 'Worker: el fallo de Brevo debe responder 502');
  assert.equal(logs.some(line => line.includes(email)), false,
    `Worker: el correo ${email} aparece en logs de error de red`);
  assert.equal(JSON.stringify(await response.json()).includes(email), false,
    'Worker: la respuesta pública contiene el correo del lector');
} finally {
  globalThis.fetch = originalFetch;
  console.error = originalError;
}
