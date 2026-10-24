import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const origin='https://davidportodiaz.com';
const listeners=new Map();
const cache={match:async()=>null,put:async()=>{},addAll:async()=>{}};
const sandbox={URL,Request,Response,Headers,console,
  caches:{open:async()=>cache,keys:async()=>[],delete:async()=>true},
  fetch:async()=>new Response('OK'),
  self:{location:{origin},addEventListener:(t,f)=>listeners.set(t,f),skipWaiting:async()=>{},clients:{claim:async()=>{}}}
};
vm.runInNewContext(readFileSync('service-worker.js','utf8'),sandbox);
const cases=[
  ['GET',origin+'/api',false],
  ['GET',origin+'/api/assistant/config?x=1',false],
  ['GET',origin+'/apiary',true],
  ['GET',origin+'/api-v2',true],
  ['GET',origin+'/assets/reading-catalogue.js',true],
  ['HEAD',origin+'/libros/',false],
  ['POST',origin+'/libros/',false],
  ['PUT',origin+'/assets/data.json',false],
  ['DELETE',origin+'/api/assistant',false],
  ['GET','https://example.org/assets/logo.png',false],
  ['GET','https://davidportodiaz.com.evil.example/api',false],
  ['GET','http://davidportodiaz.com/libros/',false]
];
for(const [method,url,expected] of cases){
  let handled=false;
  listeners.get('fetch')({
    request:{method,url,mode:'cors',destination:'',headers:new Headers()},
    respondWith(){handled=true;},waitUntil(){}
  });
  assert.equal(handled,expected,method+' '+url);
}
console.log('PASS request routing matrix: '+cases.length+' partitions');