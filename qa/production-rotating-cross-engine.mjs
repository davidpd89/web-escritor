import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import { chromium, firefox, webkit } from 'playwright';
import { assertProductionRelease } from './production-release-marker.mjs';

const O=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const S=(process.env.EXPECTED_RELEASE_SHA||'').trim();
const day=(process.env.QA_SAMPLE_DAY||new Date().toISOString().slice(0,10));
const seed=(process.env.QA_SAMPLE_SEED||`${S||'live'}:${day}:cross-engine`).trim();
const registry=JSON.parse(fs.readFileSync('data/content-registry.json','utf8'));
const defs=registry.defaults||{};

const entries=[...new Map(registry.entries
  .map(x=>({...defs,...x}))
  .filter(x=>x.status==='public'&&String(x.sourceFile||'').endsWith('.html'))
  .filter(x=>!String(x.url||'').includes('#'))
  .filter(x=>{
    try{
      const html=fs.readFileSync(x.sourceFile,'utf8');
      return html.includes('site-header')&&html.includes('data-explore-dialog');
    }catch{return false}
  })
  .map(x=>[x.url,x])).values()];

function score(route){return crypto.createHash('sha256').update(seed+'\n'+route).digest('hex')}
function pick(items,n){return items.slice().sort((a,b)=>score(a.url).localeCompare(score(b.url))).slice(0,n).map(x=>x.url)}

const groups={
  editorials:entries.filter(x=>x.url.startsWith('/editoriales/')&&x.url!=='/editoriales/'),
  tools:entries.filter(x=>x.url.startsWith('/herramientas/')&&x.url!=='/herramientas/'),
  content:entries.filter(x=>(x.url.startsWith('/cuaderno/')&&x.url!=='/cuaderno/')||x.url.startsWith('/recomendaciones/')),
  other:entries.filter(x=>!x.url.startsWith('/editoriales/')&&!x.url.startsWith('/herramientas/')&&!x.url.startsWith('/cuaderno/')&&!x.url.startsWith('/recomendaciones/')),
};
const ROUTES=[...new Set([
  ...pick(groups.editorials,2),
  ...pick(groups.tools,2),
  ...pick(groups.content,2),
  ...pick(groups.other,2),
])];
const ENGINES={chromium,firefox,webkit};
const failures=[];

await assertProductionRelease({origin:O,sha:S,label:'rotating-cross-engine'});

async function audit(engineName,browser,route){
  const context=await browser.newContext({viewport:{width:1180,height:800},reducedMotion:'reduce'});
  const page=await context.newPage();
  const pageErrors=[];
  page.on('pageerror',e=>pageErrors.push(String(e)));
  await page.route(/(?:gc\.zgo\.at|goatcounter\.com|metricool\.com|clarity\.ms|c\.bing\.com)/,r=>r.abort());
  try{
    let response=null;
    for(let attempt=0;attempt<3;attempt++){
      response=await page.goto(`${O}${route}?qa_rotating_engine=${engineName}&sample=${encodeURIComponent(day)}&attempt=${attempt}`,{waitUntil:'domcontentloaded',timeout:25000}).catch(()=>null);
      if(response&&response.status()!==429&&(response.status()<500||response.status()>599)) break;
      await page.waitForTimeout(650*(attempt+1));
    }
    assert.equal(response?.status(),200,`${engineName} ${route}: HTTP ${response?.status()}`);
    assert.equal(await page.locator('main').count(),1,`${engineName} ${route}: expected one main`);
    assert.ok((await page.locator('h1').first().innerText()).trim(),`${engineName} ${route}: empty h1`);

    const enter=page.locator('[data-intro-enter]').first();
    if(await enter.count()){
      if(await enter.isVisible().catch(()=>false)) await enter.click().catch(()=>{});
      else await page.evaluate(()=>document.querySelector('[data-intro-enter]')?.click());
      await page.waitForTimeout(250);
    }

    const trigger=page.locator('[data-explore-open]').first();
    assert.equal(await trigger.count(),1,`${engineName} ${route}: Explore trigger missing/duplicated`);
    await trigger.click();
    const dialog=page.locator('[data-explore-dialog]').first();
    await dialog.waitFor({state:'visible',timeout:3000});
    assert.equal(await dialog.evaluate(el=>Boolean(el.open)),true,`${engineName} ${route}: Explore did not open`);
    assert.equal(await page.evaluate(()=>Boolean(document.activeElement?.closest('[data-explore-dialog]'))),true,`${engineName} ${route}: focus did not enter Explore`);
    await page.keyboard.press('Escape');
    await dialog.waitFor({state:'hidden',timeout:3000});

    await page.setViewportSize({width:360,height:740});
    await page.waitForTimeout(120);
    const g=await page.evaluate(()=>({
      sw:Math.max(document.documentElement.scrollWidth,document.body?.scrollWidth||0),
      iw:innerWidth,
      h1:document.querySelector('h1')?.getBoundingClientRect().width||0,
      main:document.querySelector('main')?.getBoundingClientRect().width||0,
    }));
    assert.ok(g.sw<=g.iw+1,`${engineName} ${route}: mobile overflow ${g.sw}>${g.iw}`);
    assert.ok(g.h1>0&&g.main>0,`${engineName} ${route}: collapsed content after resize`);
    assert.deepEqual(pageErrors,[],`${engineName} ${route}: page errors ${pageErrors.join(' | ')}`);
    console.log(`PASS [${engineName}] ${route}`);
  }catch(e){
    failures.push(`[${engineName}] ${route}: ${e.message}`);
  }finally{
    await context.close();
  }
}

for(const [name,launcher] of Object.entries(ENGINES)){
  const browser=await launcher.launch({headless:true});
  try{
    for(const route of ROUTES) await audit(name,browser,route);
  }finally{
    await browser.close();
  }
}

console.log('ROTATING CROSS-ENGINE SAMPLE',JSON.stringify({seed,day,routes:ROUTES},null,2));
assert.deepEqual(failures,[],failures.join('\n'));
console.log(`PASS rotating cross-engine production smoke: ${ROUTES.length} routes x ${Object.keys(ENGINES).length} engines`);
