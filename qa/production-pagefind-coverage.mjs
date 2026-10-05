import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright';
import { assertProductionRelease } from './production-release-marker.mjs';

const O=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const S=(process.env.EXPECTED_RELEASE_SHA||'').trim();
const registry=JSON.parse(fs.readFileSync('data/content-registry.json','utf8'));
const defs=registry.defaults||{};

await assertProductionRelease({origin:O,sha:S,label:'pagefind-coverage'});

const candidates=registry.entries.map(x=>({...defs,...x}))
  .filter(x=>x.status==='public'&&x.searchIndex&&String(x.sourceFile||'').endsWith('.html')&&!String(x.url||'').includes('#'))
  .filter(x=>String(x.label||'').trim().length>=12&&String(x.label||'').trim().split(/\s+/).length>=2);

function score(s){let h=2166136261;for(const ch of String(s)){h^=ch.codePointAt(0);h=Math.imul(h,16777619)}return h>>>0}
const byTerritory=new Map();
for(const x of candidates){const k=x.territory||'sin-territorio';if(!byTerritory.has(k))byTerritory.set(k,[]);byTerritory.get(k).push(x)}
const sample=[];
for(const [territory,items] of [...byTerritory].sort(([a],[b])=>a.localeCompare(b))){
  const picked=[...items].sort((a,b)=>score(a.id)-score(b.id)).slice(0,Math.min(4,items.length));
  sample.push(...picked.map(x=>({...x,territory})));
}
assert.ok(sample.length>=12,`Pagefind distributed sample too small: ${sample.length}`);

const browser=await chromium.launch({headless:true});
const failures=[];
try{
  const context=await browser.newContext({viewport:{width:1280,height:800},reducedMotion:'reduce'});
  const page=await context.newPage();
  await page.route(/(?:gc\.zgo\.at|goatcounter\.com|metricool\.com|clarity\.ms|c\.bing\.com)/,r=>r.abort());
  const nav=await page.goto(`${O}/?qa_pagefind_coverage=${encodeURIComponent(S||'live')}`,{waitUntil:'domcontentloaded',timeout:25000});
  assert.equal(nav?.status(),200,'Pagefind coverage bootstrap failed');
  for(const x of sample){
    try{
      const results=await page.evaluate(async query=>{
        const pagefind=await import('/pagefind/pagefind.js');
        const found=await pagefind.search(query);
        return Promise.all((found.results||[]).slice(0,20).map(async r=>{const d=await r.data();return {url:d.url,title:d.meta?.title||'',score:r.score}}));
      },x.label);
      const expected=new URL(x.url,O).pathname;
      const paths=results.map(r=>new URL(r.url,O).pathname);
      assert.ok(paths.includes(expected),`${x.territory}/${x.id}: search for "${x.label}" missing ${expected}; got ${paths.join(', ')}`);
    }catch(e){failures.push(String(e?.message||e))}
  }
  await context.close();
}finally{await browser.close()}

assert.deepEqual(failures,[],failures.join('\n'));
console.log(`PASS production Pagefind distributed coverage: ${sample.length} pages across ${byTerritory.size} territories`);
