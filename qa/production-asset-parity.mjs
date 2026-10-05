import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';

const ROOT=process.cwd();
const ORIGIN=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const SHA=(process.env.EXPECTED_RELEASE_SHA||'').trim();
const MAX_EXACT=3*1024*1024;
const ALLOWED_EXT=new Set(['.css','.js','.mjs','.json','.xml','.svg','.png','.jpg','.jpeg','.webp','.avif','.woff2','.woff','.ico']);
const registry=JSON.parse(fs.readFileSync('data/content-registry.json','utf8'));
const defs=registry.defaults||{};
const htmlFiles=registry.entries.map(x=>({...defs,...x}))
  .filter(x=>x.status==='public'&&String(x.sourceFile||'').endsWith('.html'))
  .map(x=>x.sourceFile);
for(const extra of ['404.html','offline.html']) if(fs.existsSync(extra)) htmlFiles.push(extra);

const refs=new Map();
function add(raw,source){
  if(!raw||raw.startsWith('data:')||raw.startsWith('#')||raw.startsWith('mailto:')||raw.startsWith('tel:'))return;
  let u;
  try{u=new URL(raw,ORIGIN)}catch{return}
  if(u.origin!==ORIGIN)return;
  const pathname=decodeURIComponent(u.pathname);
  const ext=path.extname(pathname).toLowerCase();
  if(!ALLOWED_EXT.has(ext))return;
  const local=pathname.replace(/^\//,'');
  if(!local||!fs.existsSync(local)||!fs.statSync(local).isFile())return;
  if(!refs.has(pathname))refs.set(pathname,{pathname,queries:new Set(),sources:new Set()});
  const x=refs.get(pathname);x.queries.add(u.search);x.sources.add(source);
}
for(const file of [...new Set(htmlFiles)]){
  const html=fs.readFileSync(file,'utf8');
  for(const m of html.matchAll(/\b(?:src|href|poster)=["']([^"']+)["']/gi))add(m[1],file);
  for(const m of html.matchAll(/\bsrcset=["']([^"']+)["']/gi)){
    for(const candidate of m[1].split(',')){
      const url=candidate.trim().split(/\s+/)[0];add(url,file);
    }
  }
}
for(const file of ['manifest.json']){
  if(!fs.existsSync(file))continue;
  const data=JSON.parse(fs.readFileSync(file,'utf8'));
  for(const icon of data.icons||[])add(icon.src,file);
}

async function fetchRetry(url){
  let last;
  for(let i=0;i<4;i++){
    try{
      const r=await fetch(url,{headers:{'cache-control':'no-cache','user-agent':'david-porto-production-asset-parity/1.0'},signal:AbortSignal.timeout(20000)});
      const body=Buffer.from(await r.arrayBuffer());
      last={status:r.status,headers:r.headers,body,url:r.url};
      if(r.status!==429&&(r.status<500||r.status>599))return last;
    }catch(e){last=e}
    if(i<3)await new Promise(r=>setTimeout(r,700*(i+1)));
  }
  if(last?.status)return last;throw last;
}
async function pool(items,n,fn){let i=0;await Promise.all(Array.from({length:n},async()=>{while(true){const k=i++;if(k>=items.length)return;await fn(items[k])}}))}

if(SHA){
  const r=await fetchRetry(`${ORIGIN}/_release/${SHA}.json?qa_asset_release=1`);
  assert.equal(r.status,200,'release marker missing');
  assert.deepEqual(JSON.parse(r.body.toString('utf8')),{schemaVersion:1,sha:SHA},'release marker mismatch');
}

const failures=[],observations=[];
await pool([...refs.values()],8,async item=>{
  try{
    const local=item.pathname.replace(/^\//,'');
    const bytes=fs.readFileSync(local);
    const query=[...item.queries].find(Boolean)||'';
    const join=query ? query+'&' : '?';
    const r=await fetchRetry(`${ORIGIN}${item.pathname}${query}${join}qa_asset=${encodeURIComponent(SHA||'live')}`);
    assert.equal(r.status,200,`${item.pathname}: HTTP ${r.status}`);
    const ct=(r.headers.get('content-type')||'').toLowerCase();
    assert.doesNotMatch(ct,/text\/html/,`${item.pathname}: asset served as HTML`);
    if(bytes.length<=MAX_EXACT){
      const localHash=crypto.createHash('sha256').update(bytes).digest('hex');
      const liveHash=crypto.createHash('sha256').update(r.body).digest('hex');
      assert.equal(liveHash,localHash,`${item.pathname}: production bytes differ from audited release`);
    }else{
      assert.equal(r.body.length,bytes.length,`${item.pathname}: large asset byte length drift`);
    }
    observations.push({
      path:item.pathname,
      bytes:bytes.length,
      exact:bytes.length<=MAX_EXACT,
      cacheControl:r.headers.get('cache-control')||'',
      etag:r.headers.get('etag')||'',
      contentType:ct,
    });
  }catch(e){failures.push(String(e?.message||e))}
});
assert.deepEqual(failures,[],failures.slice(0,50).join('\n'));

const versioned=observations.filter(x=>/\.(?:css|js|mjs)$/.test(x.path));
const noCache=versioned.filter(x=>!x.cacheControl);
console.log(`PASS production asset parity: ${observations.length} referenced assets; ${observations.filter(x=>x.exact).length} exact byte comparisons`);
console.log(`CACHE observation: ${versioned.length} CSS/JS assets; ${noCache.length} without Cache-Control`);
