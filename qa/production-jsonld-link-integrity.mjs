import assert from 'node:assert/strict';
import fs from 'node:fs';
import { assertProductionRelease } from './production-release-marker.mjs';

const ORIGIN=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const SHA=(process.env.EXPECTED_RELEASE_SHA||'').trim();
const registry=JSON.parse(fs.readFileSync('data/content-registry.json','utf8'));
const defaults=registry.defaults||{};

await assertProductionRelease({origin:ORIGIN,sha:SHA,label:'jsonld-link-integrity'});

const publicSources=[...new Set(
  (registry.entries||[])
    .map(x=>({...defaults,...x}))
    .filter(x=>x.status==='public'&&String(x.sourceFile||'').endsWith('.html'))
    .map(x=>x.sourceFile)
    .filter(p=>fs.existsSync(p))
)].sort();

const JSONLD_RE=/<script\b[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi;
const forbidden=[];
const internal=new Map();
let blocks=0;

function walk(value,source,path='$'){
  if(Array.isArray(value)){
    value.forEach((v,i)=>walk(v,source,`${path}[${i}]`));
    return;
  }
  if(value&&typeof value==='object'){
    for(const [k,v] of Object.entries(value)) walk(v,source,`${path}.${k}`);
    return;
  }
  if(typeof value!=='string') return;
  const raw=value.trim();
  if(!raw) return;
  if(/https?:\/\/(?:localhost|127\.0\.0\.1)(?::\d+)?(?:\/|$)/i.test(raw)){
    forbidden.push(`${source} ${path}: local/dev URL ${raw}`);
    return;
  }
  if(/^http:\/\/davidportodiaz\.com(?:\/|$)/i.test(raw)){
    forbidden.push(`${source} ${path}: insecure first-party URL ${raw}`);
    return;
  }
  if(!raw.startsWith(ORIGIN+'/')&&raw!==ORIGIN) return;
  let u;
  try{u=new URL(raw)}catch{forbidden.push(`${source} ${path}: invalid first-party URL ${raw}`);return}
  if(u.origin!==ORIGIN) return;
  u.hash='';
  const fetchUrl=u.toString();
  if(!internal.has(fetchUrl)) internal.set(fetchUrl,[]);
  internal.get(fetchUrl).push(`${source} ${path}`);
}

for(const source of publicSources){
  const html=fs.readFileSync(source,'utf8');
  for(const match of html.matchAll(JSONLD_RE)){
    blocks++;
    let data;
    try{data=JSON.parse(match[1])}
    catch(e){throw new Error(`${source}: invalid JSON-LD reached live reference audit: ${e.message}`)}
    walk(data,source);
  }
}

assert.deepEqual(forbidden,[],forbidden.join('\n'));
assert.ok(blocks>=100,`suspiciously few JSON-LD blocks scanned: ${blocks}`);
assert.ok(internal.size>=25,`suspiciously few internal JSON-LD URLs: ${internal.size}`);

async function checkOne(url){
  let last;
  for(let attempt=0;attempt<3;attempt++){
    try{
      const u=new URL(url);
      u.searchParams.set('__qa_jsonld',SHA||'live');
      const r=await fetch(u,{
        redirect:'follow',
        headers:{'cache-control':'no-cache','user-agent':'david-porto-jsonld-integrity/1.0'},
        signal:AbortSignal.timeout(20000),
      });
      if(r.status===200) return;
      if(r.status!==429&&(r.status<500||r.status>599)){
        throw new Error(`HTTP ${r.status}`);
      }
      last=new Error(`transient HTTP ${r.status}`);
    }catch(e){last=e}
    if(attempt<2) await new Promise(r=>setTimeout(r,500*(attempt+1)));
  }
  throw new Error(`${url}: ${last?.message||last}; referenced by ${internal.get(url).slice(0,4).join(' | ')}`);
}

const urls=[...internal.keys()];
const failures=[];
let next=0;
async function worker(){
  while(true){
    const i=next++;
    if(i>=urls.length) return;
    try{await checkOne(urls[i])}catch(e){failures.push(String(e?.message||e))}
  }
}
await Promise.all(Array.from({length:Math.min(10,urls.length)},()=>worker()));
assert.deepEqual(failures,[],failures.join('\n'));

console.log(`PASS production JSON-LD link integrity: ${blocks} blocks across ${publicSources.length} public sources; ${urls.length} unique first-party URLs live`);
