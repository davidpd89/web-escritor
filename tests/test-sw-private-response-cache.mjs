import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const origin='https://davidportodiaz.com';
const scenarios=[
  {'Cache-Control':'no-store'},
  {'Cache-Control':'private, max-age=60'},
  {'Set-Cookie':'session=private; HttpOnly; Secure'}
];
for(const headers of scenarios){
  const listeners=new Map(), writes=[];
  const cache={match:async()=>null,put:async(req,res)=>{writes.push(req.url);},addAll:async()=>{}};
  const sandbox={URL,Request,Response,Headers,console,
    caches:{open:async()=>cache,keys:async()=>[],delete:async()=>true},
    fetch:async()=>new Response('<html><body>Privado</body></html>',{status:200,headers}),
    self:{location:{origin},addEventListener:(t,f)=>listeners.set(t,f),skipWaiting:async()=>{},clients:{claim:async()=>{}}}
  };
  vm.runInNewContext(readFileSync('service-worker.js','utf8'),sandbox);
  let result;
  listeners.get('fetch')({
    request:{method:'GET',url:origin+'/cuaderno/?sesion=privada',mode:'navigate',destination:'document',headers:new Headers()},
    respondWith(p){result=p;},waitUntil(){}
  });
  assert.ok(result);
  assert.equal((await result).status,200);
  assert.equal(writes.length,0,'Respuesta restringida almacenada: '+JSON.stringify(headers));
}
console.log('PASS private/no-store navigation');