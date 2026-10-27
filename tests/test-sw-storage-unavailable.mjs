import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const listeners=new Map();
const origin='https://davidportodiaz.com';
let networkCalls=0;
const sandbox={URL,Request,Response,Headers,console,
  caches:{open:async()=>{throw new Error('CacheStorage unavailable');},keys:async()=>[],delete:async()=>true},
  fetch:async()=>{networkCalls++;return new Response('<h1>Página disponible</h1>',{status:200});},
  self:{location:{origin},addEventListener:(t,f)=>listeners.set(t,f),skipWaiting:async()=>{},clients:{claim:async()=>{}}}
};
vm.runInNewContext(readFileSync('service-worker.js','utf8'),sandbox);
let result;
listeners.get('fetch')({
  request:{method:'GET',url:origin+'/libros/',mode:'navigate',destination:'document',headers:new Headers()},
  respondWith(p){result=p;},waitUntil(){}
});
assert.ok(result);
let response;
try{response=await result;}catch(e){assert.fail('La navegación falló por CacheStorage: '+e.message);}
assert.equal(networkCalls,1);
assert.equal(response.status,200);
assert.match(await response.text(),/Página disponible/);
console.log('PASS navigation without CacheStorage');