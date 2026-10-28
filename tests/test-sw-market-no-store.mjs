import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const listeners=new Map();
const origin='https://davidportodiaz.com';
const writes=[];
const cache={
  match:async()=>new Response('{"version":"vieja"}'),
  put:async(req,res)=>writes.push(await res.text()),
  addAll:async()=>{}
};
const sandbox={URL,Request,Response,Headers,console,
  caches:{open:async()=>cache,keys:async()=>[],delete:async()=>true},
  fetch:async()=>new Response('{"version":"actual"}',{status:200,headers:{'Content-Type':'application/json'}}),
  self:{location:{origin},addEventListener:(type,fn)=>listeners.set(type,fn),skipWaiting:async()=>{},clients:{claim:async()=>{}}}
};
vm.runInNewContext(readFileSync('service-worker.js','utf8'),sandbox);
const handler=listeners.get('fetch');
assert.equal(typeof handler,'function');
let result;
const event={
  request:{method:'GET',url:origin+'/assets/reading-market.json',mode:'cors',cache:'no-store',destination:'',headers:new Headers()},
  respondWith(p){result=Promise.resolve(p);},
  waitUntil(){}
};
handler(event);
assert.ok(result,'El Service Worker no interceptó la petición');
const response=await result;
assert.equal(response.status,200);
assert.deepEqual(JSON.parse(await response.text()),{version:'actual'},'cache:no-store recibió datos antiguos');
console.log('PASS market JSON no-store');