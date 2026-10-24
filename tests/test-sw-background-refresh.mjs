import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const origin='https://davidportodiaz.com';
const listeners=new Map(), waiters=[];
let stored=new Response('PORTADA_VIEJA');
let writes=0;
const cache={
  match:async()=>stored.clone(),
  put:async(req,res)=>{stored=res.clone();writes++;},
  addAll:async()=>{}
};
const sandbox={URL,Request,Response,Headers,console,
  caches:{open:async()=>cache,keys:async()=>[],delete:async()=>true},
  fetch:async()=>new Response('PORTADA_NUEVA',{status:200}),
  self:{location:{origin},addEventListener:(t,f)=>listeners.set(t,f),skipWaiting:async()=>{},clients:{claim:async()=>{}}}
};
vm.runInNewContext(readFileSync('service-worker.js','utf8'),sandbox);
let response;
listeners.get('fetch')({
  request:{method:'GET',url:origin+'/assets/reading-covers/example.webp',mode:'cors',destination:'image',headers:new Headers()},
  respondWith(p){response=p;},waitUntil(p){waiters.push(Promise.resolve(p));}
});
assert.equal(await (await response).text(),'PORTADA_VIEJA');
assert.equal(waiters.length,1,'Falta la tarea de revalidación');
await Promise.all(waiters);
assert.equal(writes,1);
assert.equal(await (await cache.match()).text(),'PORTADA_NUEVA');
console.log('PASS stale-while-revalidate updates stored response');