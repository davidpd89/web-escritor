import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const listeners=new Map();
let skipCalls=0, claimCalls=0, addCalls=0;
const origin='https://davidportodiaz.com';
const cache={
  addAll:async()=>{addCalls++;throw new Error('Asset missing from APP_SHELL');},
  match:async()=>null,
  put:async()=>{}
};
const sandbox={URL,Request:class extends Request { constructor(input, init) { super(typeof input === 'string' || input instanceof URL ? new URL(input, origin) : input, init); } },Response,Headers,console,
  caches:{open:async()=>cache,keys:async()=>[],delete:async()=>true},
  fetch:async()=>new Response('ok'),
  self:{location:{origin},addEventListener:(t,f)=>listeners.set(t,f),skipWaiting:async()=>{skipCalls++;},clients:{claim:async()=>{claimCalls++;}}}
};
vm.runInNewContext(readFileSync('service-worker.js','utf8'),sandbox);
let installation;
listeners.get('install')({waitUntil(p){installation=Promise.resolve(p);}});
assert.ok(installation,'La instalación no registró waitUntil');
await assert.rejects(installation,/Asset missing/);
assert.equal(addCalls,1);
assert.equal(skipCalls,0,'Se activó un worker con precarga incompleta');
assert.equal(claimCalls,0,'Se reclamaron clientes durante una instalación fallida');
console.log('PASS atomic installation failure');