import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright';
import { assertProductionRelease } from './production-release-marker.mjs';

const O=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const S=(process.env.EXPECTED_RELEASE_SHA||'').trim();
const registry=JSON.parse(fs.readFileSync('data/content-registry.json','utf8'));
const defs=registry.defaults||{};
const pages=registry.entries.map(x=>({...defs,...x}))
  .filter(x=>x.status==='public'&&String(x.sourceFile||'').endsWith('.html')&&fs.existsSync(x.sourceFile));
const stateHashPaths=new Set(['/editoriales/']);

await assertProductionRelease({origin:O,sha:S,label:'cross-page-fragments'});

const refs=[];
for(const page of pages){
  const html=fs.readFileSync(page.sourceFile,'utf8');
  const base=new URL(page.url,O);
  for(const m of html.matchAll(/<a\b[^>]*\bhref=["']([^"']+)["']/gi)){
    const raw=m[1].trim();
    if(!raw||raw.startsWith('mailto:')||raw.startsWith('tel:')||raw.startsWith('javascript:')) continue;
    let target;
    try{target=new URL(raw,base)}catch{continue}
    if(target.origin!==O||!target.hash) continue;
    if(target.pathname===base.pathname) continue;
    const encoded=target.hash.slice(1);
    if(!encoded) continue;
    if(stateHashPaths.has(target.pathname)&&encoded.includes('=')) continue;
    let fragment=encoded;
    try{fragment=decodeURIComponent(encoded)}catch{}
    refs.push({from:page.url,targetPath:target.pathname,fragment,raw});
  }
}

assert.ok(refs.length>0,'No cross-page fragment references found; audit setup is probably stale');

const unique=[...new Map(refs.map(x=>[x.targetPath+'#'+x.fragment,x])).values()];
const byPath=new Map();
for(const ref of unique){
  if(!byPath.has(ref.targetPath)) byPath.set(ref.targetPath,[]);
  byPath.get(ref.targetPath).push(ref);
}

const browser=await chromium.launch({headless:true});
const failures=[];
try{
  const context=await browser.newContext({viewport:{width:1280,height:800},reducedMotion:'reduce'});
  for(const [path,targets] of byPath){
    const page=await context.newPage();
    await page.route(/(?:gc\.zgo\.at|goatcounter\.com|metricool\.com|clarity\.ms|c\.bing\.com)/,r=>r.abort());
    try{
      const response=await page.goto(`${O}${path}?qa_cross_fragment=${encodeURIComponent(S||'live')}`,{waitUntil:'domcontentloaded',timeout:25000});
      assert.equal(response?.status(),200,`${path}: HTTP ${response?.status()}`);
      for(const ref of targets){
        const exists=await page.evaluate(id=>Boolean(document.getElementById(id)||document.querySelector(`[name="${CSS.escape(id)}"]`)),ref.fragment);
        assert.equal(exists,true,`${ref.from} -> ${ref.raw}: target ${ref.targetPath}#${ref.fragment} does not exist in production DOM`);
      }
    }catch(e){
      failures.push(String(e?.message||e));
    }finally{
      await page.close();
    }
  }
  await context.close();
}finally{
  await browser.close();
}

assert.deepEqual(failures,[],failures.join('\n'));
console.log(`PASS production cross-page fragments: ${unique.length} unique fragment targets across ${byPath.size} destination routes`);
