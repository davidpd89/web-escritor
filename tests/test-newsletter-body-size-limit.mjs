import assert from 'node:assert/strict';
import worker from '../cloudflare-worker-subscribe.js';

let calls = 0;
const original = globalThis.fetch;
globalThis.fetch = async () => { calls++; return new Response('{}', {status:201}); };
try {
  const body = JSON.stringify({email:'reader@example.com',source:'home',padding:'x'.repeat(20000)});
  const request = new Request('https://subscribe.example.workers.dev/',{method:'POST',headers:{Origin:'https://davidportodiaz.com','Content-Type':'application/json'},body});
  const env = {BREVO_API_KEY:'test',BREVO_LIST_ID:'3',BREVO_DOI_TEMPLATE_ID:'42',BREVO_DOI_REDIRECT_URL:'https://davidportodiaz.com/gracias-suscripcion/',RATE_LIMITER:{limit:async()=>({success:true})}};
  const response = await worker.fetch(request,env);
  assert.ok([400,413].includes(response.status),`Un cuerpo de ${body.length} bytes no debe aceptarse: ${response.status}`);
  assert.equal(calls,0,'No debe invocarse Brevo');
} finally { globalThis.fetch = original; }
console.log('newsletter body size: OK');