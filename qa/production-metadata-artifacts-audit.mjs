import assert from 'node:assert/strict';
import fs from 'node:fs';

const ORIGIN=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const SHA=(process.env.EXPECTED_RELEASE_SHA||'').trim().toLowerCase();
const read=p=>fs.readFileSync(p,'utf8');
const norm=s=>String(s||'').replace(/\r\n?/g,'\n').trim();

function attrs(tag){
  const out={};
  for(const m of tag.matchAll(/([:\w-]+)\s*=\s*(["'])(.*?)\2/gs)) out[m[1].toLowerCase()]=m[3];
  return out;
}
function meta(html,key,value){
  for(const tag of html.match(/<meta\b[^>]*>/gi)||[]){
    const a=attrs(tag);
    if((a[key]||'').toLowerCase()===value.toLowerCase()) return a.content||'';
  }
  return '';
}
function canonical(html){
  for(const tag of html.match(/<link\b[^>]*>/gi)||[]){
    const a=attrs(tag);
    if((a.rel||'').toLowerCase().split(/\s+/).includes('canonical')) return a.href||'';
  }
  return '';
}
function robots(html){
  return meta(html,'name','robots').toLowerCase().split(',').map(x=>x.trim()).filter(Boolean).sort();
}
function jsonld(html,label){
  const docs=[];
  let i=0;
  for(const m of html.matchAll(/<script\b[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi)){
    i++;
    try{docs.push(JSON.parse(m[1]))}catch(e){throw new Error(`${label}: invalid JSON-LD #${i}: ${e.message}`)}
  }
  return docs;
}
async function request(route){
  const u=new URL(route,ORIGIN);
  u.searchParams.set('__qa_meta',SHA||Date.now().toString(36));
  let last;
  for(let i=0;i<4;i++){
    try{
      const r=await fetch(u,{redirect:'follow',headers:{'cache-control':'no-cache','user-agent':'david-porto-production-metadata-artifacts/1.0'},signal:AbortSignal.timeout(20000)});
      const body=await r.text();
      last={status:r.status,headers:r.headers,body,url:r.url};
      if(r.status!==429&&(r.status<500||r.status>599)) return last;
    }catch(e){last=e}
    if(i<3) await new Promise(r=>setTimeout(r,700*(i+1)));
  }
  if(last?.status!==undefined) return last;
  throw last;
}
async function pool(xs,n,fn){
  let i=0;
  await Promise.all(Array.from({length:n},async()=>{
    while(true){
      const k=i++;
      if(k>=xs.length)return;
      await fn(xs[k]);
    }
  }));
}

if(SHA){
  const r=await request('/_release/'+SHA+'.json');
  assert.equal(r.status,200,'release marker missing');
  assert.deepEqual(JSON.parse(r.body),{schemaVersion:1,sha:SHA},'release marker mismatch');
}

const registry=JSON.parse(read('data/content-registry.json'));
const defs=registry.defaults||{};
const pages=registry.entries.map(x=>({...defs,...x}))
  .filter(x=>x.status==='public'&&String(x.sourceFile||'').endsWith('.html'));

const fields=[
  ['name','description'],
  ['name','robots'],
  ['property','og:title'],
  ['property','og:description'],
  ['property','og:url'],
  ['property','og:type'],
  ['property','og:image'],
  ['name','twitter:card'],
  ['name','twitter:title'],
  ['name','twitter:description'],
  ['name','twitter:image'],
];
const failures=[];
await pool(pages,10,async x=>{
  try{
    const local=read(x.sourceFile);
    const prod=await request(x.url);
    assert.equal(prod.status,200,`${x.url}: HTTP ${prod.status}`);
    const ct=(prod.headers.get('content-type')||'').toLowerCase();
    assert.match(ct,/text\/html|application\/xhtml\+xml/,`${x.url}: HTML content-type ${ct}`);

    assert.equal(canonical(prod.body),canonical(local),`${x.url}: canonical drift`);
    assert.deepEqual(robots(prod.body),robots(local),`${x.url}: robots drift`);
    for(const [kind,key] of fields){
      assert.equal(meta(prod.body,kind,key),meta(local,kind,key),`${x.url}: ${key} drift`);
    }
    assert.deepEqual(jsonld(prod.body,x.url),jsonld(local,x.sourceFile),`${x.url}: JSON-LD drift`);

    const c=canonical(prod.body);
    const og=meta(prod.body,'property','og:url');
    if(c&&og) assert.equal(og,c,`${x.url}: og:url differs from canonical`);
    for(const [kind,key] of [['property','og:image'],['name','twitter:image']]){
      const v=meta(prod.body,kind,key);
      if(v) assert.doesNotThrow(()=>new URL(v),`${x.url}: invalid ${key}`);
    }
  }catch(e){failures.push(String(e?.message||e))}
});

const artifacts=[
  {route:'/manifest.json',file:'manifest.json',type:/application\/(?:manifest\+json|json)|text\/json/i,validate:b=>JSON.parse(b)},
  {route:'/sitemap.xml',file:'sitemap.xml',type:/(?:application|text)\/xml/i,validate:b=>assert.match(b,/<urlset\b/i)},
  {route:'/editoriales-sitemap.xml',file:'editoriales-sitemap.xml',type:/(?:application|text)\/xml/i,validate:b=>assert.match(b,/<urlset\b/i)},
  {route:'/cuaderno/feed.xml',file:'cuaderno/feed.xml',type:/(?:application|text)\/(?:atom\+)?xml/i,validate:b=>assert.match(b,/<(?:feed|rss)\b/i)},
  {route:'/convocatorias-escritores/deadlines.ics',file:'convocatorias-escritores/deadlines.ics',type:null,validate:b=>{assert.match(b,/BEGIN:VCALENDAR/);assert.match(b,/END:VCALENDAR/)}},
  {route:'/convocatorias-escritores/opportunities.json',file:'convocatorias-escritores/opportunities.json',type:/application\/json|text\/json/i,validate:b=>JSON.parse(b)},
  {route:'/editoriales/editoriales-data.json',file:'editoriales/editoriales-data.json',type:/application\/json|text\/json/i,validate:b=>JSON.parse(b)},
];
for(const a of artifacts){
  const r=await request(a.route);
  assert.equal(r.status,200,`${a.route}: HTTP ${r.status}`);
  const ct=(r.headers.get('content-type')||'').toLowerCase();
  assert.doesNotMatch(ct,/text\/html/,`${a.route}: artifact served as HTML`);
  if(a.type) assert.match(ct,a.type,`${a.route}: unexpected content-type ${ct}`);
  a.validate(r.body);
  assert.equal(norm(r.body),norm(read(a.file)),`${a.route}: production artifact differs from release`);
}

assert.deepEqual(failures,[],failures.slice(0,60).join('\n'));
console.log(`PASS production metadata/artifacts: ${pages.length} public HTML routes + ${artifacts.length} non-HTML artifacts`);
