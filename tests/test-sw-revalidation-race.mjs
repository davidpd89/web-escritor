import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const origin='https://davidportodiaz.com';
const listeners=new Map(), deferred=[],waiters=[];
let stored=new Response('ORIGINAL');
const cache={match:async()=>stored.clone(),put:async(req,res)=>{stored=res.clone();},addAll:async()=>{}};
const sandbox={URL,Request,Response,Headers,console,
  caches:{open:async()=>cache,keys:async()=>[],delete:async()=>true},
  fetch:()=>new Promise(resolve=>deferred.push(resolve)),
  self:{location:{origin},addEventListener:(t,f)=>listeners.set(t,f),skipWaiting:async()=>{},clients:{claim:async()=>{}}}
};
vm.runInNewContext(readFileSync('service-worker.js','utf8'),sandbox);
const request={method:'GET',url:origin+'/assets/reading-covers/concurrent.webp',mode:'cors',destination:'image',headers:new Headers()};
function dispatch(){
  let response;
  listeners.get('fetch')({request,respondWith(p){response=p;},waitUntil(p){waiters.push(Promise.resolve(p));}});
  return response;
}
const first=dispatch(),second=dispatch();
assert.equal(await (await first).text(),'ORIGINAL');
assert.equal(await (await second).text(),'ORIGINAL');
assert.equal(deferred.length,2);
assert.equal(waiters.length,2);
deferred[1](new Response('VERSION_B_MAS_RECIENTE'));
await waiters[1];
assert.equal(await stored.clone().text(),'VERSION_B_MAS_RECIENTE');
deferred[0](new Response('VERSION_A_ANTIGUA'));
await waiters[0];
assert.equal(await stored.clone().text(),'VERSION_B_MAS_RECIENTE','Una respuesta tardía sobrescribió la versión más reciente');
console.log('PASS concurrent revalidation ordering');