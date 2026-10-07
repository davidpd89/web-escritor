import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { assertProductionRelease } from './production-release-marker.mjs';

const O=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const S=(process.env.EXPECTED_RELEASE_SHA||'').trim();
const ROUTES=['/','/editoriales/','/convocatorias-escritores/','/herramientas/','/asistente/','/mapa-del-sitio/'];
const VIEWPORTS=[
  {width:390,height:320,label:'keyboard-like-portrait'},
  {width:320,height:390,label:'narrow-short-portrait'},
];

await assertProductionRelease({origin:O,sha:S,label:'short-viewport-history'});

const browser=await chromium.launch({headless:true});
const failures=[];

async function dismissIntro(page){
  const enter=page.locator('[data-intro-enter]').first();
  if(await enter.count()){
    await page.evaluate(()=>document.querySelector('[data-intro-enter]')?.click());
    const intro=page.locator('[data-intro]').first();
    if(await intro.count()) await intro.waitFor({state:'hidden',timeout:3000}).catch(()=>{});
  }
}

async function assertShortViewport(page,route,vp){
  const r=await page.goto(`${O}${route}?qa_short_viewport=${vp.label}`,{waitUntil:'domcontentloaded',timeout:25000});
  assert.equal(r?.status(),200,`${route} ${vp.label}: HTTP ${r?.status()}`);
  await dismissIntro(page);
  await page.waitForTimeout(180);
  const state=await page.evaluate(()=>({
    sw:Math.max(document.documentElement.scrollWidth,document.body?.scrollWidth||0),
    iw:innerWidth,
    h1:(document.querySelector('h1')?.innerText||'').trim(),
    main:(document.querySelector('main')?.innerText||'').trim().length,
    blockers:[...document.querySelectorAll('body *')].filter(el=>{
      const s=getComputedStyle(el),b=el.getBoundingClientRect();
      return (s.position==='fixed'||s.position==='sticky')&&s.display!=='none'&&s.visibility!=='hidden'&&
        b.width>innerWidth*.9&&b.height>innerHeight*.78;
    }).map(el=>({tag:el.tagName.toLowerCase(),id:el.id||'',cls:String(el.className||'').slice(0,120)})),
  }));
  assert.ok(state.h1,`${route} ${vp.label}: missing H1`);
  assert.ok(state.main>100,`${route} ${vp.label}: critical content missing`);
  assert.ok(state.sw<=state.iw+1,`${route} ${vp.label}: horizontal overflow ${state.sw}>${state.iw}`);
  assert.deepEqual(state.blockers,[],`${route} ${vp.label}: viewport-blocking fixed/sticky UI ${JSON.stringify(state.blockers)}`);

  const explore=page.locator('[data-explore-open]').first();
  if(await explore.count() && await explore.isVisible().catch(()=>false)){
    await explore.click();
    const dialog=page.locator('[data-explore-dialog]').first();
    await dialog.waitFor({state:'visible',timeout:3000});
    // The panel slides in, so it is "visible" while still translated off-screen
    // (seen at left:-359 on production). Wait for the transition to settle;
    // if it never lands inside the viewport the assertion below still fails.
    await dialog.evaluate(el=>new Promise(res=>{
      const t0=performance.now();
      const tick=()=>{const b=el.getBoundingClientRect();
        if((b.left>=-1&&b.right<=innerWidth+1)||performance.now()-t0>1500) res(); else requestAnimationFrame(tick)};
      tick();
    }));
    const g=await dialog.evaluate(el=>{
      const b=el.getBoundingClientRect(),s=getComputedStyle(el);
      const descendantScrollable=[...el.querySelectorAll('*')].some(n=>{
        const cs=getComputedStyle(n);
        return ['auto','scroll'].includes(cs.overflowY)&&n.scrollHeight>n.clientHeight;
      });
      return {left:b.left,top:b.top,right:b.right,bottom:b.bottom,overflowY:s.overflowY,scrollable:el.scrollHeight<=el.clientHeight+1||['auto','scroll'].includes(s.overflowY)||descendantScrollable};
    });
    assert.ok(g.left>=-1&&g.top>=-1&&g.right<=vp.width+1&&g.bottom<=vp.height+1,`${route} ${vp.label}: Explore dialog escapes viewport ${JSON.stringify(g)}`);
    assert.equal(g.scrollable,true,`${route} ${vp.label}: Explore dialog cannot scroll in short viewport`);
    await page.keyboard.press('Escape');
  }
}

try{
  for(const vp of VIEWPORTS){
    const context=await browser.newContext({viewport:{width:vp.width,height:vp.height},isMobile:true,hasTouch:true,reducedMotion:'reduce'});
    for(const route of ROUTES){
      const page=await context.newPage();
      const errors=[];
      page.on('pageerror',e=>errors.push(String(e)));
      try{
        await assertShortViewport(page,route,vp);
        assert.deepEqual(errors,[],`${route} ${vp.label}: page errors ${errors.join(' | ')}`);
      }catch(e){failures.push(String(e?.message||e))}
      finally{await page.close()}
    }
    await context.close();
  }

  // Full navigation away/back is different from pushState-only Back/Forward:
  // it exercises browser page restoration or reload-from-URL after a real document change.
  {
    const context=await browser.newContext({viewport:{width:390,height:700},isMobile:true,hasTouch:true,reducedMotion:'reduce'});
    const page=await context.newPage();
    const start=`${O}/editoriales/?qa_cross_page_history=1#estado=open&pais=${encodeURIComponent('España')}`;
    try{
      const r=await page.goto(start,{waitUntil:'domcontentloaded',timeout:25000});
      assert.equal(r?.status(),200,'cross-page history: initial HTTP');
      await page.waitForFunction(()=>document.querySelector('[data-editoriales-status]')?.value==='open');
      await page.locator('[data-editoriales-search]').fill('Planeta');
      await page.waitForFunction(()=>location.hash.includes('q=Planeta'));
      const before=page.url();

      const target=page.locator('[data-editorial-card]:not([hidden]) a[href^="/editoriales/"]').first();
      assert.ok(await target.count(),'cross-page history: no visible editorial detail link');
      await Promise.all([
        page.waitForLoadState('domcontentloaded'),
        target.click(),
      ]);
      assert.notEqual(page.url(),before,'cross-page history: navigation did not leave directory');

      await page.goBack({waitUntil:'domcontentloaded',timeout:25000});
      await page.waitForFunction(()=>document.querySelector('[data-editoriales-status]')?.value==='open');
      assert.equal(await page.locator('[data-editoriales-country]').inputValue(),'España','cross-page history: country not restored');
      assert.equal(await page.locator('[data-editoriales-search]').inputValue(),'Planeta','cross-page history: search not restored');
      assert.ok(page.url().includes('q=Planeta'),'cross-page history: URL hash state lost after Back');
      const bad=await page.locator('[data-editorial-card]:not([hidden])').evaluateAll(cards=>cards.filter(c=>c.dataset.status!=='open'||c.dataset.country!=='España'||!c.textContent.toLowerCase().includes('planeta')).map(c=>c.dataset.name));
      assert.deepEqual(bad,[],'cross-page history: visible cards no longer match restored state');
    }catch(e){failures.push(String(e?.message||e))}
    finally{await context.close()}
  }
}finally{
  await browser.close();
}

assert.deepEqual(failures,[],failures.join('\n'));
console.log(`PASS short viewport + cross-page history: ${ROUTES.length} routes x ${VIEWPORTS.length} viewports + Editoriales navigation restoration`);
