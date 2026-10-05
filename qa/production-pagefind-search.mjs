import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const O=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const S=(process.env.EXPECTED_RELEASE_SHA||'').trim();
const failures=[];

async function retryFetch(url){
  let last;
  for(let i=0;i<3;i++){
    try{
      const r=await fetch(url,{headers:{'cache-control':'no-cache','user-agent':'david-porto-production-pagefind/1.0'},signal:AbortSignal.timeout(15000)});
      if(r.status!==429&&(r.status<500||r.status>599)) return r;
      last=new Error('transient HTTP '+r.status+' '+url);
    }catch(e){last=e}
    await new Promise(r=>setTimeout(r,700*(i+1)));
  }
  throw last;
}
if(S){
  const r=await retryFetch(`${O}/_release/${S}.json?qa_pagefind_release=1`);
  assert.equal(r.status,200,'release marker missing');
  assert.deepEqual(await r.json(),{schemaVersion:1,sha:S},'release marker mismatch');
}

const browser=await chromium.launch({headless:true});
try{
  const context=await browser.newContext({viewport:{width:1280,height:800},reducedMotion:'reduce'});
  const page=await context.newPage();
  await page.route(/(?:gc\.zgo\.at|goatcounter\.com|metricool\.com|clarity\.ms|c\.bing\.com)/,r=>r.abort());
  const errors=[];
  page.on('pageerror',e=>errors.push(String(e)));
  const nav=await page.goto(`${O}/?qa_live_pagefind=1`,{waitUntil:'domcontentloaded',timeout:25000});
  assert.equal(nav?.status(),200,'home navigation failed');

  const pf=await page.request.get(`${O}/pagefind/pagefind.js?qa_live_pagefind=1`);
  assert.equal(pf.status(),200,'deployed pagefind.js missing');
  assert.match((pf.headers()['content-type']||'').toLowerCase(),/(javascript|text\/plain)/,'pagefind.js wrong MIME');

  async function search(query){
    return page.evaluate(async q=>{
      const pagefind=await import('/pagefind/pagefind.js');
      const result=await pagefind.search(q);
      return Promise.all((result.results||[]).slice(0,10).map(async r=>{
        const d=await r.data();
        return {url:d.url,title:d.meta?.title||'',excerpt:d.excerpt||'',score:r.score};
      }));
    },query);
  }

  const cases=[
    ['Las manecillas del recuerdo',/\/las-manecillas-del-recuerdo\//],
    ['Samuel entre mundos',/\/(libros\/samuel-entre-mundos|fragmento)\//],
    ['editoriales',/\/editoriales\//],
    ['convocatorias',/\/convocatorias-escritores\//],
    ['contador de palabras',/\/herramientas\/contador-palabras\//],
  ];
  for(const [q,re] of cases){
    const results=await search(q);
    assert.ok(results.length>0,`"${q}" returned zero results`);
    assert.ok(results.some(x=>re.test(x.url)),`"${q}" missing expected destination: ${JSON.stringify(results)}`);
    assert.ok(results.every(x=>x.url.startsWith('/')&&!x.url.startsWith('//')),`"${q}" returned non-local URL`);
    assert.ok(results.every(x=>x.title.trim()),`"${q}" returned empty title`);
    for(const x of results.slice(0,3)){
      const r=await retryFetch(new URL(x.url,O));
      assert.equal(r.status,200,`search result is not live: ${x.url}`);
    }
  }

  const plain=await search('fantasia');
  const accented=await search('fantasía');
  assert.ok(plain.length>0&&accented.length>0,'accent variants must both return results');
  assert.ok(plain.some(a=>accented.some(b=>a.url===b.url)),'accent variants should share at least one destination');

  const zero=await search('zzqqwwjjkk99inexistente');
  assert.equal(zero.length,0,'nonsense query must return zero results');

  for(const q of ['política de privacidad datos personales','aviso legal responsabilidad']){
    const results=await search(q);
    assert.equal(results.some(x=>x.url==='/privacidad.html'||x.url==='/aviso-legal.html'),false,`noindex/legal page leaked for "${q}"`);
  }
  const gated=await search('dónde empieza la jaula');
  assert.equal(gated.some(x=>x.url.includes('donde-empieza-la-jaula')),false,'gated route leaked into production search');
  assert.deepEqual(errors,[],'page errors: '+errors.join(' | '));
  await context.close();
}catch(e){
  failures.push(String(e?.message||e));
}finally{
  await browser.close();
}
assert.deepEqual(failures,[],failures.join('\n'));
console.log('PASS production Pagefind: deployed index, ranking smoke, accents, exclusions and live result URLs');
