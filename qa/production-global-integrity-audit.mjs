import assert from 'node:assert/strict';
import fs from 'node:fs';

const ORIGIN=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const SHA=(process.env.EXPECTED_RELEASE_SHA||'').trim().toLowerCase();
const read=p=>fs.readFileSync(p,'utf8');
const norm=s=>String(s||'').replace(/\r\n?/g,'\n').trim();
const strip=s=>norm(String(s||'').replace(/<script\b[\s\S]*?<\/script>/gi,' ').replace(/<style\b[\s\S]*?<\/style>/gi,' ').replace(/<[^>]*>/g,' ').replace(/\s+/g,' '));
const title=h=>strip(h.match(/<title\b[^>]*>([\s\S]*?)<\/title>/i)?.[1]||'');
const h1=h=>strip(h.match(/<h1\b[^>]*>([\s\S]*?)<\/h1>/i)?.[1]||'');
const canonical=h=>[...(h.match(/<link\b[^>]*>/gi)||[])].find(x=>/rel=["'][^"']*canonical/i.test(x))?.match(/href=["']([^"']+)/i)?.[1]||'';
const noindex=h=>/name=["']robots["'][^>]*content=["'][^"']*noindex/i.test(h);
const metaRefresh=h=>/<meta\b[^>]*http-equiv=["']refresh["']/i.test(h);
const htmlLang=h=>h.match(/<html\b[^>]*\blang=["']([^"']+)/i)?.[1]||'';
const locs=x=>[...x.matchAll(/<loc>(.*?)<\/loc>/gis)].map(m=>m[1].trim());

async function get(route){
  const u=new URL(route,ORIGIN);
  u.searchParams.set('__qa_global',SHA||Date.now().toString(36));
  let last;
  for(let i=0;i<3;i++){
    try{
      const r=await fetch(u,{redirect:'follow',headers:{'cache-control':'no-cache','user-agent':'david-porto-global-production-integrity/1.0'},signal:AbortSignal.timeout(20000)});
      return {status:r.status,body:await r.text(),url:r.url,headers:r.headers};
    }catch(e){last=e;await new Promise(r=>setTimeout(r,800*(i+1)))}
  }
  throw last;
}
async function pool(xs,n,fn){
  let i=0;
  await Promise.all(Array.from({length:n},async()=>{
    while(true){
      const k=i++;
      if(k>=xs.length) return;
      await fn(xs[k],k);
    }
  }));
}

if(SHA){
  const r=await get('/_release/'+SHA+'.json');
  assert.equal(r.status,200,'release marker missing');
  assert.deepEqual(JSON.parse(r.body),{schemaVersion:1,sha:SHA},'release marker mismatch');
}

const registry=JSON.parse(read('data/content-registry.json'));
const defs=registry.defaults||{};
const entries=registry.entries.map(x=>({...defs,...x}));
const pages=entries.filter(x=>x.status==='public'&&String(x.sourceFile||'').endsWith('.html')&&!metaRefresh(read(x.sourceFile)));

const failures=[];
await pool(pages,12,async x=>{
  try{
    const local=read(x.sourceFile);
    const r=await get(x.url);
    assert.equal(r.status,200,x.url+' status');
    const ct=(r.headers.get('content-type')||'').toLowerCase();
    assert.match(ct,/text\/html|application\/xhtml\+xml/,x.url+' content-type '+ct);

    const final=new URL(r.url);
    assert.equal(final.origin,ORIGIN,x.url+' origin redirect');
    assert.equal(final.pathname,new URL(x.url,ORIGIN).pathname,x.url+' path redirect');

    const body=r.body;
    assert.ok(body.length>300,x.url+' suspiciously small HTML');
    assert.equal(title(body),title(local),x.url+' title drift');
    assert.equal(h1(body),h1(local),x.url+' h1 drift');
    assert.equal(htmlLang(body),htmlLang(local),x.url+' lang drift');

    const lc=canonical(local), pc=canonical(body);
    if(lc||pc) assert.equal(pc,lc,x.url+' canonical drift');
    if(x.searchIndex) assert.equal(noindex(body),false,x.url+' accidental noindex');

    const visible=strip(body);
    assert.ok(visible.length>80,x.url+' soft-empty visible content');
    assert.doesNotMatch(visible,/\b404\b|página no encontrada|page not found/i,x.url+' soft-404 signal');
  }catch(e){failures.push(String(e?.message||e))}
});

for(const [route,file] of [
  ['/robots.txt','robots.txt'],
  ['/manifest.json','manifest.json'],
  ['/service-worker.js','service-worker.js'],
  ['/humans.txt','humans.txt'],
  ['/llms.txt','llms.txt'],
  ['/llms-full.txt','llms-full.txt'],
]){
  const r=await get(route);
  assert.equal(r.status,200,route+' status');
  assert.equal(norm(r.body),norm(read(file)),route+' differs from repository release');
}

const prodSitemap=await get('/sitemap.xml');
assert.equal(prodSitemap.status,200,'sitemap production status');
const localLocs=locs(read('sitemap.xml'));
const prodLocs=locs(prodSitemap.body);
assert.deepEqual(prodLocs,localLocs,'production sitemap differs from repository sitemap');
assert.equal(new Set(prodLocs).size,prodLocs.length,'duplicate production sitemap URLs');

for(const x of entries.filter(x=>x.status==='public'&&x.sitemap)){
  assert.ok(prodLocs.includes(new URL(x.url,ORIGIN).href),'production sitemap missing '+x.url);
}

for(const badRoute of ['/__qa-global-missing__','/editoriales/__qa-global-missing__/','/convocatorias-escritores/__qa-global-missing__/']){
  const r=await get(badRoute);
  assert.equal(r.status,404,badRoute+' must be a real 404');
  assert.doesNotMatch(r.body,/name=["']robots["'][^>]*content=["'][^"']*index/i,badRoute+' 404 must not be indexable');
}

assert.deepEqual(failures,[],failures.slice(0,40).join('\n'));
console.log('PASS global production integrity: '+pages.length+' public HTML routes + sitemap + real 404 semantics');
