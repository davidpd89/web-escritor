import assert from 'node:assert/strict';
import worker from '../cloudflare-worker-subscribe.js';
const original=globalThis.fetch;
let calls=0;
globalThis.fetch=async()=>{calls++;return new Response('{}',{status:201});};
const env={BREVO_API_KEY:'test',BREVO_LIST_ID:'3',BREVO_DOI_TEMPLATE_ID:'42',BREVO_DOI_REDIRECT_URL:'https://davidportodiaz.com/gracias-suscripcion/',RATE_LIMITER:{limit:async()=>({success:true})}};
try {
  for(const website of [true,1,{},['spam']]) {
    calls=0;
    const request=new Request('https://subscribe.example.workers.dev/',{method:'POST',headers:{Origin:'https://davidportodiaz.com','Content-Type':'application/json'},body:JSON.stringify({email:'reader@example.com',source:'home',website})});
    const response=await worker.fetch(request,env);
    assert.equal(calls,0,`Honeypot ${JSON.stringify(website)} llegó a Brevo`);
    assert.ok([201,400].includes(response.status));
  }
} finally {globalThis.fetch=original;}
console.log('newsletter honeypot types: OK');