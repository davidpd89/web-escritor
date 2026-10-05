import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { assertProductionRelease } from './production-release-marker.mjs';

const O=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const S=(process.env.EXPECTED_RELEASE_SHA||'').trim();
const ROUTES=[
  '/',
  '/las-manecillas-del-recuerdo/',
  '/cuaderno/',
  '/herramientas/',
  '/asistente/',
  '/editoriales/',
  '/convocatorias-escritores/',
  '/mapa-del-sitio/',
];

await assertProductionRelease({origin:O,sha:S,label:'session-resilience'});

const browser=await chromium.launch({headless:true});
const failures=[];

async function dismissIntro(page){
  const enter=page.locator('[data-intro-enter]').first();
  if(await enter.count()){
    if(await enter.isVisible().catch(()=>false)) await enter.click();
    else await page.evaluate(()=>document.querySelector('[data-intro-enter]')?.click());
    const intro=page.locator('[data-intro]').first();
    if(await intro.count()) await intro.waitFor({state:'hidden',timeout:3000}).catch(()=>{});
  }
}

async function assertUsable(page,route,label){
  await dismissIntro(page);
  await page.waitForTimeout(120);
  const state=await page.evaluate(()=>({
    h1:(document.querySelector('h1')?.innerText||'').trim(),
    main:(document.querySelector('main')?.innerText||'').trim().length,
    sw:Math.max(document.documentElement.scrollWidth,document.body?.scrollWidth||0),
    iw:innerWidth,
  }));
  assert.ok(state.h1,`${label} ${route}: missing H1`);
  assert.ok(state.main>100,`${label} ${route}: critical content missing`);
  assert.ok(state.sw<=state.iw+1,`${label} ${route}: horizontal overflow ${state.sw}>${state.iw}`);
}

try{
  // Simulate privacy/browser configurations where Web Storage operations throw.
  // Critical navigation/content must remain usable even if preferences cannot persist.
  {
    const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,reducedMotion:'reduce'});
    await context.addInitScript(()=>{
      const blocked=()=>{throw new DOMException('Storage disabled by browser policy','SecurityError')};
      for(const name of ['getItem','setItem','removeItem','clear']){
        try{Object.defineProperty(Storage.prototype,name,{value:blocked,configurable:true,writable:true})}catch{}
      }
    });
    for(const route of ROUTES){
      const page=await context.newPage();
      const errors=[];
      page.on('pageerror',e=>errors.push(String(e)));
      try{
        const r=await page.goto(`${O}${route}?qa_storage_blocked=1`,{waitUntil:'domcontentloaded',timeout:25000});
        assert.equal(r?.status(),200,`storage ${route}: HTTP ${r?.status()}`);
        await assertUsable(page,route,'storage');
        assert.deepEqual(errors,[],`storage ${route}: uncaught errors ${errors.join(' | ')}`);
      }catch(e){failures.push(e.message)}finally{await page.close()}
    }
    await context.close();
  }

  // Resize the live page through both orientations instead of testing isolated snapshots.
  {
    const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,reducedMotion:'reduce'});
    for(const route of ROUTES){
      const page=await context.newPage();
      const errors=[];
      page.on('pageerror',e=>errors.push(String(e)));
      try{
        const r=await page.goto(`${O}${route}?qa_orientation=1`,{waitUntil:'domcontentloaded',timeout:25000});
        assert.equal(r?.status(),200,`orientation ${route}: HTTP ${r?.status()}`);
        await assertUsable(page,route,'portrait-before');
        await page.setViewportSize({width:844,height:390});
        await page.waitForTimeout(180);
        await assertUsable(page,route,'landscape-live');
        await page.setViewportSize({width:390,height:844});
        await page.waitForTimeout(180);
        await assertUsable(page,route,'portrait-after');
        assert.deepEqual(errors,[],`orientation ${route}: uncaught errors ${errors.join(' | ')}`);
      }catch(e){failures.push(e.message)}finally{await page.close()}
    }
    await context.close();
  }
}finally{
  await browser.close();
}

assert.deepEqual(failures,[],failures.join('\n'));
console.log(`PASS production session resilience: ${ROUTES.length} routes with blocked storage + live orientation changes`);
