import assert from 'node:assert/strict';
import worker from '../cloudflare-worker-subscribe.js';
const keys=[];
const env={BREVO_API_KEY:'test',BREVO_LIST_ID:'3',BREVO_DOI_TEMPLATE_ID:'42',BREVO_DOI_REDIRECT_URL:'https://davidportodiaz.com/gracias-suscripcion/',RATE_LIMITER:{limit:async input=>{keys.push(input.key);return {success:true};}}};
const original=globalThis.fetch;
globalThis.fetch=async()=>new Response('{}',{status:201});
try {
  for(const email of ['Reader@Example.com','reader@example.com',' READER@EXAMPLE.COM ']) {
    const request=new Request('https://subscribe.example.workers.dev/',{method:'POST',headers:{Origin:'https://davidportodiaz.com','Content-Type':'application/json'},body:JSON.stringify({email,source:'home'})});
    assert.equal((await worker.fetch(request,env)).status,201);
  }
  assert.equal(keys.length,3);
  assert.equal(new Set(keys).size,1,'La capitalización permite crear distintas claves de limitación');
  for(const key of keys) {assert.match(key,/^newsletter:[a-f0-9]{64}$/);assert.doesNotMatch(key,/@/);}
} finally {globalThis.fetch=original;}
console.log('newsletter rate key case: OK');