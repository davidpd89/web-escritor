import assert from 'node:assert/strict';
import worker from '../cloudflare-worker-subscribe.js';
const origins=['http://davidportodiaz.com','https://www.davidportodiaz.com','https://davidportodiaz.com.evil.test','https://evil.test.davidportodiaz.com','https://davidportodiaz.com:8443','https://davidportodiaz.com@evil.test','null',''];
for(const origin of origins){
  for(const method of ['OPTIONS','POST']){
    const request=new Request('https://subscribe.example.workers.dev/',{method,headers:{Origin:origin,'Content-Type':'application/json'},...(method==='POST'?{body:JSON.stringify({email:'reader@example.com',source:'home'})}:{})});
    const response=await worker.fetch(request,{});
    assert.equal(response.headers.get('Access-Control-Allow-Origin'),null,`${origin}: CORS autorizado`);
    if(method==='POST')assert.equal(response.status,403,`${origin}: POST autorizado`);
  }
}
console.log('newsletter origin confusables: OK');