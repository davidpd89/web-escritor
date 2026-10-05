import assert from 'node:assert/strict';
import { assertProductionRelease } from './production-release-marker.mjs';
import {chromium} from 'playwright';

const O=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const S=(process.env.EXPECTED_RELEASE_SHA||'').trim();
const PRO=['/editoriales/','/convocatorias-escritores/','/metodologia-editorial/'];
const ROUTES=[...new Set([
  '/',
  '/libros/',
  '/las-manecillas-del-recuerdo/',
  '/libros/samuel-entre-mundos/',
  '/cuaderno/',
  '/herramientas/',
  '/asistente/',
  '/eventos.html',
  '/ferias.html',
  '/mapa-del-sitio/',
  '/prensa.html',
  '/lectores-beta/',
  ...PRO,
])];

await assertProductionRelease({origin:O,sha:S,label:'adaptive'});

const browser=await chromium.launch({headless:true});
const errs=[];

async function core(page,route,label){
  const r=await page.goto(`${O}${route}?qa_${label}=1`,{waitUntil:'domcontentloaded',timeout:20000});
  assert.equal(r?.status(),200,`${label} ${route}: HTTP ${r?.status()}`);
  const enter=page.locator('[data-intro-enter]').first();
  if(await enter.count()){
    await page.evaluate(()=>document.querySelector('[data-intro-enter]')?.click());
    const intro=page.locator('[data-intro]').first();
    if(await intro.count()) await intro.waitFor({state:'hidden',timeout:2500}).catch(()=>{});
  }
  await page.waitForTimeout(120);
  const g=await page.evaluate(()=>({
    w:Math.max(document.documentElement.scrollWidth,document.body?.scrollWidth||0),
    v:innerWidth,
    h:(document.querySelector('h1')?.innerText||'').trim(),
    m:(document.querySelector('main')?.innerText||'').trim().length,
  }));
  assert.ok(g.h&&g.m>120,`${label} ${route}: missing critical content`);
  assert.ok(g.w<=g.v+1,`${label} ${route}: horizontal overflow ${g.w}>${g.v}`);
}

async function eachRoute(context,label,fn){
  for(const route of ROUTES){
    const page=await context.newPage();
    try{
      await fn(page,route);
    }catch(e){
      errs.push(`${label} ${route}: ${e.message}`);
    }finally{
      await page.close();
    }
  }
}

try{
  {
    const c=await browser.newContext({viewport:{width:1280,height:900}});
    await eachRoute(c,'print',async(page,route)=>{
      await page.emulateMedia({media:'print'});
      await core(page,route,'print');
      const fixed=await page.evaluate(()=>[...document.querySelectorAll('body *')]
        .filter(e=>{
          const s=getComputedStyle(e),r=e.getBoundingClientRect();
          return s.position==='fixed'&&s.display!=='none'&&s.visibility!=='hidden'&&
            r.width>innerWidth*.5&&r.height>innerHeight*.12;
        })
        .map(e=>({tag:e.tagName.toLowerCase(),id:e.id||'',className:typeof e.className==='string'?e.className:''})));
      assert.deepEqual(fixed,[],`large fixed overlay ${JSON.stringify(fixed)}`);
    });
    await c.close();
  }

  {
    const c=await browser.newContext({
      viewport:{width:390,height:844},
      isMobile:true,
      hasTouch:true,
      reducedMotion:'reduce',
    });
    await eachRoute(c,'motion',async(page,route)=>{
      await core(page,route,'motion');
      assert.equal(await page.evaluate(()=>matchMedia('(prefers-reduced-motion: reduce)').matches),true);
      const offenders=await page.evaluate(()=>[...document.querySelectorAll('body *')]
        .filter(e=>{
          const s=getComputedStyle(e);
          return s.animationIterationCount==='infinite'&&parseFloat(s.animationDuration)>.25;
        })
        .map(e=>({tag:e.tagName.toLowerCase(),id:e.id||'',className:typeof e.className==='string'?e.className:''})));
      assert.deepEqual(offenders,[],`infinite animations ${JSON.stringify(offenders.slice(0,8))}`);
    });
    await c.close();
  }

  {
    const c=await browser.newContext({viewport:{width:390,height:844},forcedColors:'active'});
    await eachRoute(c,'forced',async(page,route)=>{
      await core(page,route,'forced');
      assert.equal(await page.evaluate(()=>matchMedia('(forced-colors: active)').matches),true);
      const controls=await page.locator('main a[href]:visible,main button:visible,main input:visible,main select:visible,main textarea:visible').count();
      assert.ok(controls>0,'no visible interactive controls in main');
    });
    await c.close();
  }

  {
    const c=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
    await eachRoute(c,'fonts',async(page,route)=>{
      await page.route(/\.(woff2?|ttf|otf)(\?|$)/i,r=>r.abort());
      await core(page,route,'fonts');
    });
    await c.close();
  }
}finally{
  await browser.close();
}

assert.deepEqual(errs,[],errs.join('\n'));
console.log(`PASS adaptive formats across ${ROUTES.length} representative routes: print, reduced-motion, forced-colors, font fallback`);
