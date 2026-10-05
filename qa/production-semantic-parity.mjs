import assert from 'node:assert/strict';
import fs from 'node:fs';

const O=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const S=(process.env.EXPECTED_RELEASE_SHA||'').trim().toLowerCase();
const read=p=>fs.readFileSync(p,'utf8');
const attr=(tag,name)=>{
  const re=new RegExp(`\\b${name.replace(':','\\:')}\\s*=\\s*(["'])(.*?)\\1`,'i');
  return tag.match(re)?.[2]||'';
};
const tags=(html,name)=>html.match(new RegExp(`<${name}\\b[^>]*>`,'gi'))||[];
const meta=(html,key,value)=>{
  for(const tag of tags(html,'meta')){
    if(attr(tag,key).toLowerCase()===value.toLowerCase()) return attr(tag,'content');
  }
  return '';
};
const canonical=(html)=>{
  for(const tag of tags(html,'link')){
    if(attr(tag,'rel').toLowerCase().split(/\s+/).includes('canonical')) return attr(tag,'href');
  }
  return '';
};
const title=html=>(html.match(/<title\b[^>]*>([\s\S]*?)<\/title>/i)?.[1]||'').replace(/\s+/g,' ').trim();
const h1s=html=>[...html.matchAll(/<h1\b[^>]*>([\s\S]*?)<\/h1>/gi)].map(m=>m[1].replace(/<[^>]*>/g,' ').replace(/\s+/g,' ').trim()).filter(Boolean);
const htmlLang=html=>attr(html.match(/<html\b[^>]*>/i)?.[0]||'','lang').toLowerCase();
const charset=html=>{
  for(const tag of tags(html,'meta')){
    const direct=attr(tag,'charset');
    if(direct) return direct.toLowerCase();
    if(attr(tag,'http-equiv').toLowerCase()==='content-type'){
      const m=attr(tag,'content').match(/charset\s*=\s*([^;\s]+)/i);
      if(m) return m[1].toLowerCase();
    }
  }
  return '';
};
const jsonld=html=>{
  const out=[];
  for(const m of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)){
    if(attr(`<script ${m[1]}>`,'type').toLowerCase()!=='application/ld+json') continue;
    const raw=m[2].trim();
    if(!raw) continue;
    out.push(JSON.parse(raw));
  }
  return out;
};
const semantic=html=>({
  title:title(html),
  description:meta(html,'name','description'),
  canonical:canonical(html),
  lang:htmlLang(html),
  charset:charset(html),
  viewport:meta(html,'name','viewport'),
  h1s:h1s(html),
  og:{
    title:meta(html,'property','og:title'),
    description:meta(html,'property','og:description'),
    url:meta(html,'property','og:url'),
    image:meta(html,'property','og:image'),
    type:meta(html,'property','og:type'),
  },
  twitter:{
    card:meta(html,'name','twitter:card'),
    title:meta(html,'name','twitter:title'),
    description:meta(html,'name','twitter:description'),
    image:meta(html,'name','twitter:image'),
  },
  jsonld:jsonld(html),
  counts:{
    canonical:tags(html,'link').filter(t=>attr(t,'rel').toLowerCase().split(/\s+/).includes('canonical')).length,
    description:tags(html,'meta').filter(t=>attr(t,'name').toLowerCase()==='description').length,
    viewport:tags(html,'meta').filter(t=>attr(t,'name').toLowerCase()==='viewport').length,
  }
});

async function get(route){
  const u=new URL(route,O);
  u.searchParams.set('__qa_semantic',S||Date.now().toString(36));
  let last;
  for(let i=0;i<3;i++){
    try{
      const r=await fetch(u,{
        redirect:'follow',
        headers:{'cache-control':'no-cache','user-agent':'david-porto-production-semantic-parity/1.0'},
        signal:AbortSignal.timeout(20000),
      });
      const body=await r.text();
      if(r.status!==429&&(r.status<500||r.status>599)) return {r,body};
      last=new Error(`${route}: transient HTTP ${r.status}`);
    }catch(e){last=e}
    if(i<2) await new Promise(r=>setTimeout(r,700*(i+1)));
  }
  throw last;
}
async function pool(xs,n,fn){
  let i=0;
  await Promise.all(Array.from({length:n},async()=>{
    while(true){
      const k=i++;
      if(k>=xs.length)return;
      await fn(xs[k],k);
    }
  }));
}

if(S){
  const {r,body}=await get(`/_release/${S}.json`);
  assert.equal(r.status,200,'release marker missing');
  assert.deepEqual(JSON.parse(body),{schemaVersion:1,sha:S},'release marker mismatch');
}

const registry=JSON.parse(read('data/content-registry.json'));
const defs=registry.defaults||{};
const pages=registry.entries
  .map(x=>({...defs,...x}))
  .filter(x=>x.status==='public'&&String(x.sourceFile||'').endsWith('.html'))
  .filter(x=>!/<meta\b[^>]*http-equiv=["']refresh["']/i.test(read(x.sourceFile)));

const failures=[];
await pool(pages,10,async x=>{
  try{
    const localHtml=read(x.sourceFile);
    const local=semantic(localHtml);
    const {r,body}=await get(x.url);
    assert.equal(r.status,200,`${x.url}: HTTP ${r.status}`);
    const prod=semantic(body);

    assert.deepEqual(prod,local,`${x.url}: deployed semantic metadata drift`);

    assert.equal(prod.lang,'es',`${x.url}: html lang must be es`);
    assert.match(prod.charset,/^utf-?8$/,`${x.url}: charset must be UTF-8`);
    assert.match(prod.viewport,/width\s*=\s*device-width/i,`${x.url}: viewport must use device-width`);
    assert.equal(prod.counts.viewport,1,`${x.url}: duplicate/missing viewport`);
    assert.equal(prod.counts.description,1,`${x.url}: duplicate/missing description`);
    assert.equal(prod.h1s.length,1,`${x.url}: expected exactly one H1, got ${prod.h1s.length}`);

    if(x.searchIndex||x.sitemap){
      const expected=new URL(x.url,O).href;
      assert.equal(prod.counts.canonical,1,`${x.url}: duplicate/missing canonical`);
      assert.equal(prod.canonical,expected,`${x.url}: canonical must be self-referential`);
      assert.ok(prod.description.trim().length>=40,`${x.url}: description suspiciously short`);
    }
    if(prod.og.url) assert.equal(prod.og.url,prod.canonical,`${x.url}: og:url must match canonical`);
    for(const [i,obj] of prod.jsonld.entries()) assert.ok(obj&&typeof obj==='object',`${x.url}: JSON-LD #${i+1} must parse to an object`);
  }catch(e){
    failures.push(String(e?.message||e));
  }
});

assert.deepEqual(failures,[],failures.slice(0,60).join('\n'));
console.log(`PASS production semantic parity: ${pages.length} public HTML routes`);
