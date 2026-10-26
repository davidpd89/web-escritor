import assert from 'node:assert/strict';
import fs from 'node:fs';
import {fileURLToPath} from 'node:url';

const BASE=(process.env.SITE_BASE_URL||'http://127.0.0.1:8765').replace(/\/$/,'');
const css=fs.readFileSync('assets/v1-fonts.css','utf8');
const urls=[...new Set([...css.matchAll(/url\(['"]?([^)'"\s]+\.woff2)['"]?\)/g)].map(m=>m[1]))];
assert(urls.length>=5,`assets/v1-fonts.css: solo ${urls.length} fuentes WOFF2 declaradas`);
const targets=urls.map(u=>new URL(u,`${BASE}/assets/v1-fonts.css`).href);
const requests=targets.flatMap(url=>Array.from({length:4},(_,i)=>({url,i})));
await Promise.all(requests.map(async({url,i})=>{
  const response=await fetch(url,{signal:AbortSignal.timeout(15000)});
  assert.equal(response.status,200,`${url} petición ${i}: HTTP ${response.status}`);
  const body=new Uint8Array(await response.arrayBuffer());
  assert(body.length>100,`${url} petición ${i}: fuente vacía o incompleta (${body.length} bytes)`);
  assert.equal(String.fromCharCode(...body.slice(0,4)),'wOF2',`${url} petición ${i}: cabecera WOFF2 inválida`);
}));
console.log(`PASS ${requests.length} font requests across ${targets.length} assets`);