import assert from 'node:assert/strict';
import worker from '../cloudflare-worker-subscribe.js';
const original=globalThis.fetch;
let calls=0;
globalThis.fetch=async()=>{calls++;return new Response('{}',{status:201});};
const env={BREVO_API_KEY:'test',BREVO_LIST_ID:'3',BREVO_DOI_TEMPLATE_ID:'42',BREVO_DOI_REDIRECT_URL:'https://davidportodiaz.com/gracias-suscripcion/',RATE_LIMITER:{limit:async()=>({success:true})}};
try {
  const emails=['a'.repeat(65)+'@example.com','reader@'+'a'.repeat(250)+'.com','a'.repeat(64)+'@'+'b'.repeat(190)+'.com'];
  for(const email of emails){
    calls=0;
    const request=new Request('https://subscribe.example.workers.dev/',{method:'POST',headers:{Origin:'https://davidportodiaz.com','Content-Type':'application/json'},body:JSON.stringify({email,source:'home'})});
    const response=await worker.fetch(request,env);
    assert.equal(response.status,400,`Correo de ${email.length} caracteres aceptado`);
    assert.equal(calls,0,'Brevo no debe recibir un correo inválido');
  }
} finally {globalThis.fetch=original;}
console.log('newsletter email boundary lengths: OK');