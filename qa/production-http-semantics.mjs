import assert from 'node:assert/strict';
import fs from 'node:fs';
import { assertProductionRelease } from './production-release-marker.mjs';

const O=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const S=(process.env.EXPECTED_RELEASE_SHA||'').trim();
const registry=JSON.parse(fs.readFileSync('data/content-registry.json','utf8'));
const defs=registry.defaults||{};

await assertProductionRelease({origin:O,sha:S,label:'http-semantics'});

function score(s){let h=0x811c9dc5;for(const ch of String(s)){h^=ch.codePointAt(0);h=Math.imul(h,0x01000193)}return h>>>0}
const pages=registry.entries.map(x=>({...defs,...x}))
  .filter(x=>x.status==='public'&&String(x.sourceFile||'').endsWith('.html')&&!String(x.url||'').includes('#'));
const groups=new Map();
for(const x of pages){const k=x.territory||x.type||'other';if(!groups.has(k))groups.set(k,[]);groups.get(k).push(x)}
const sample=[];
for(const [,items] of [...groups].sort(([a],[b])=>a.localeCompare(b))){sample.push(...[...items].sort((a,b)=>score(a.id)-score(b.id)).slice(0,5))}
assert.ok(sample.length>=15,`HTTP sample too small: ${sample.length}`);

async function request(url,opts={}){
  let last;
  for(let i=0;i<3;i++){
    try{
      const r=await fetch(url,{redirect:'follow',headers:{'cache-control':'no-cache','user-agent':'david-porto-http-semantics/1.0',...(opts.headers||{})},signal:AbortSignal.timeout(15000),...opts});
      if(r.status!==429&&(r.status<500||r.status>599)) return r;
      last=new Error(`transient HTTP ${r.status} ${url}`);
    }catch(e){last=e}
    if(i<2)await new Promise(r=>setTimeout(r,600*(i+1)));
  }
  throw last;
}

const failures=[];
for(const x of sample){
  try{
    const u=`${O}${x.url}${String(x.url).includes('?')?'&':'?'}qa_http=${encodeURIComponent(S||'live')}`;
    const get=await request(u);
    const head=await request(u,{method:'HEAD'});
    assert.equal(get.status,200,`${x.url}: GET ${get.status}`);
    assert.equal(head.status,200,`${x.url}: HEAD ${head.status}`);
    const getType=(get.headers.get('content-type')||'').toLowerCase();
    const headType=(head.headers.get('content-type')||'').toLowerCase();
    assert.match(getType,/text\/html|application\/xhtml\+xml/,`${x.url}: GET content-type ${getType}`);
    assert.match(headType,/text\/html|application\/xhtml\+xml/,`${x.url}: HEAD content-type ${headType}`);
    assert.equal(await head.text(),' ',`${x.url}: impossible sentinel`);
  }catch(e){
    const msg=String(e?.message||e);
    if(msg.includes('impossible sentinel')){
      // Fetch HEAD bodies are required to be empty; keep the assertion explicit
      // without consuming/normalizing a potentially absent body stream.
      try{
        const u=`${O}${x.url}${String(x.url).includes('?')?'&':'?'}qa_http_head=${encodeURIComponent(S||'live')}`;
        const head=await request(u,{method:'HEAD'});
        assert.equal((await head.arrayBuffer()).byteLength,0,`${x.url}: HEAD unexpectedly returned a body`);
      }catch(inner){failures.push(String(inner?.message||inner))}
    }else failures.push(msg);
  }
}

for(const route of ['/__qa-http-missing__','/editoriales/__qa-http-missing__/']){
  const r=await request(`${O}${route}?qa_http_404=1`,{method:'HEAD'});
  assert.equal(r.status,404,`${route}: HEAD must preserve 404 semantics`);
}

for(const media of [
  ['/assets/video/hero-tinta-david-porto.mp4','video/mp4'],
  ['/assets/video/hero-tinta-david-porto.webm','video/webm'],
]){
  const [path,type]=media;
  const r=await request(`${O}${path}?qa_range=1`,{headers:{range:'bytes=0-1023'}});
  assert.ok(r.status===200||r.status===206,`${path}: range request HTTP ${r.status}`);
  assert.match((r.headers.get('content-type')||'').toLowerCase(),new RegExp(type.replace('/','\\/')),`${path}: wrong MIME`);
  const bytes=Buffer.from(await r.arrayBuffer());
  assert.ok(bytes.length>0,`${path}: empty media response`);
  if(r.status===206){
    assert.match(r.headers.get('content-range')||'',/^bytes 0-\d+\/\d+$/i,`${path}: invalid Content-Range`);
    assert.ok(bytes.length<=1024,`${path}: partial response larger than requested range`);
  }
}

assert.deepEqual(failures,[],failures.join('\n'));
console.log(`PASS production HTTP semantics: ${sample.length} HTML routes + HEAD 404 + media range/MIME`);
