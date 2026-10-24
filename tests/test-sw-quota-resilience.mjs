import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const origin='https://davidportodiaz.com';
const listeners=new Map();
let networkCalls=0;
const cache={
  match:async()=>new Response('VERSION_ANTIGUA'),
  put:async()=>{const e=new Error('Quota exceeded');e.name='QuotaExceededError';throw e;},
  addAll:async()=>{}
};
const sandbox={URL,Request,Response,Headers,console,
  caches:{open:async()=>cache,keys:async()=>[],delete:async()=>true},
  fetch:async()=>{networkCalls++;return new Response('VERSION_NUEVA',{status:200});},
  self:{location:{origin},addEventListener:(t,f)=>listeners.set(t,f),skipWaiting:async()=>{},clients:{claim:async()=>{}}}
};
vm.runInNewContext(readFileSync('service-worker.js','utf8'),sandbox);
let result;
listeners.get('fetch')({
  request:{method:'GET',url:origin+'/assets/reading-catalogue.js',mode:'cors',destination:'script',headers:new Headers()},
  respondWith(p){result=p;},waitUntil(){}
});
assert.ok(result);
const response=await result;
assert.equal(networkCalls,1);
assert.equal(response.status,200);
assert.equal(await response.text(),'VERSION_NUEVA','Un fallo de almacenamiento ocultó la respuesta nueva');
console.log('PASS quota failure cannot replace healthy network');