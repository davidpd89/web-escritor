import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const origin='https://davidportodiaz.com';
const listeners=new Map();
const sandbox={URL,Request,Response,Headers,console,
  caches:{open:async()=>({match:async()=>null,put:async()=>{},addAll:async()=>{}}),keys:async()=>[],delete:async()=>true},
  fetch:async()=>new Response('ok'),
  self:{location:{origin},addEventListener:(t,f)=>listeners.set(t,f),skipWaiting:async()=>{},clients:{claim:async()=>{}}}
};
vm.runInNewContext(readFileSync('service-worker.js','utf8'),sandbox);
const cases=[
  {path:'/assets/audio.mp3',destination:'audio',range:null,handled:false},
  {path:'/assets/trailer.mp4',destination:'video',range:null,handled:false},
  {path:'/assets/cover.webp',destination:'image',range:'bytes=0-1023',handled:false},
  {path:'/assets/v1-shell.css',destination:'style',range:'bytes=100-',handled:false},
  {path:'/assets/cover.webp',destination:'image',range:null,handled:true},
  {path:'/assets/v1-shell.css',destination:'style',range:null,handled:true},
  {path:'/assets/video.mp4',destination:'',range:'bytes=-100',handled:false}
];
for(const row of cases){
  let handled=false;
  const headers=new Headers(row.range?{Range:row.range}:{});
  listeners.get('fetch')({
    request:{method:'GET',url:origin+row.path,mode:'cors',destination:row.destination,headers},
    respondWith(){handled=true;},waitUntil(){}
  });
  assert.equal(handled,row.handled,JSON.stringify(row));
}
console.log('PASS media/range routing');