import assert from 'node:assert/strict';
import worker from '../cloudflare-worker-subscribe.js';
const env={BREVO_API_KEY:'test',BREVO_LIST_ID:'3',BREVO_DOI_TEMPLATE_ID:'42',BREVO_DOI_REDIRECT_URL:'https://davidportodiaz.com/gracias-suscripcion/',RATE_LIMITER:{limit:async()=>({success:true})}};
const original=globalThis.fetch;
globalThis.fetch=async()=>new Response('{}',{status:201});
try {
  for(const email of ['reader@example.com','invalid']) {
    const request=new Request('https://subscribe.example.workers.dev/',{method:'POST',headers:{Origin:'https://davidportodiaz.com','Content-Type':'application/json'},body:JSON.stringify({email,source:'home'})});
    const response=await worker.fetch(request,env);
    assert.match(response.headers.get('Cache-Control')||'',/\bno-store\b/i,`Respuesta ${response.status} sin no-store`);
  }
} finally {globalThis.fetch=original;}
console.log('newsletter response cache: OK');