import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { assertProductionRelease } from './production-release-marker.mjs';

const O=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const S=(process.env.EXPECTED_RELEASE_SHA||'').trim();
const ROUTES=[
  '/',
  '/las-manecillas-del-recuerdo/',
  '/libros/samuel-entre-mundos/',
  '/cuaderno/',
  '/herramientas/',
  '/asistente/',
  '/editoriales/',
  '/convocatorias-escritores/',
  '/metodologia-editorial/',
  '/prensa.html',
  '/mapa-del-sitio/',
];

await assertProductionRelease({origin:O,sha:S,label:'nojs-history'});

const browser=await chromium.launch({headless:true});
const failures=[];
try{
  {
    const context=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844},isMobile:true,hasTouch:true});
    for(const route of ROUTES){
      const page=await context.newPage();
      try{
        const response=await page.goto(`${O}${route}?qa_nojs=1`,{waitUntil:'domcontentloaded',timeout:25000});
        assert.equal(response?.status(),200,`no-js ${route}: HTTP ${response?.status()}`);
        const state=await page.evaluate(()=>({
          h1:(document.querySelector('h1')?.textContent||'').trim(),
          main:(document.querySelector('main')?.textContent||'').replace(/\s+/g,' ').trim().length,
          nav:[...document.querySelectorAll('.primary-nav a[href]')].filter(a=>{const s=getComputedStyle(a),r=a.getBoundingClientRect();return s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0;}).length,
          blockers:[...document.querySelectorAll('[data-intro],[data-consent-banner],dialog[open]')].filter(el=>{const s=getComputedStyle(el),r=el.getBoundingClientRect();return s.display!=='none'&&s.visibility!=='hidden'&&Number(s.opacity||1)>.05&&r.width>innerWidth*.75&&r.height>innerHeight*.35;}).map(el=>el.id||(el.hasAttribute('data-intro')?'intro':el.hasAttribute('data-consent-banner')?'consent':el.tagName.toLowerCase())),
          sw:Math.max(document.documentElement.scrollWidth,document.body?.scrollWidth||0),iw:innerWidth,
        }));
        assert.ok(state.h1,`no-js ${route}: missing H1`);
        assert.ok(state.main>100,`no-js ${route}: critical content missing`);
        assert.ok(state.nav>0,`no-js ${route}: fallback primary navigation missing`);
        assert.deepEqual(state.blockers,[],`no-js ${route}: blocking overlay ${JSON.stringify(state.blockers)}`);
        assert.ok(state.sw<=state.iw+1,`no-js ${route}: horizontal overflow ${state.sw}>${state.iw}`);
      }catch(e){failures.push(String(e?.message||e))}finally{await page.close()}
    }
    await context.close();
  }

  {
    const context=await browser.newContext({viewport:{width:1280,height:850},reducedMotion:'reduce'});
    const page=await context.newPage();
    await page.route(/(?:gc\.zgo\.at|goatcounter\.com|metricool\.com|clarity\.ms|c\.bing\.com)/,r=>r.abort());
    try{
      const start=`${O}/editoriales/?utm_source=qa-history#estado=open&pais=${encodeURIComponent('España')}`;
      const response=await page.goto(start,{waitUntil:'domcontentloaded',timeout:25000});
      assert.equal(response?.status(),200,'history: editoriales initial HTTP');
      await page.waitForFunction(()=>document.querySelector('[data-editoriales-status]')?.value==='open');
      assert.equal(await page.locator('[data-editoriales-country]').inputValue(),'España','history: deep-linked country not restored');
      const visibleOpen=await page.locator('[data-editorial-card]:not([hidden])').count();
      assert.ok(visibleOpen>0,'history: deep-linked open filter returned zero cards');
      const badInitial=await page.locator('[data-editorial-card]:not([hidden])').evaluateAll(cards=>cards.filter(c=>c.dataset.status!=='open'||c.dataset.country!=='España').map(c=>c.dataset.name));
      assert.deepEqual(badInitial,[],'history: initial visible cards do not match deep-linked filters');
      await page.locator('[data-editoriales-search]').fill('Planeta');
      await page.waitForFunction(()=>location.hash.includes('q=Planeta'));
      assert.equal(new URL(page.url()).searchParams.get('utm_source'),'qa-history','history: search replaceState dropped query string');
      await page.locator('[data-editoriales-status]').selectOption('closed');
      await page.waitForFunction(()=>document.querySelector('[data-editoriales-status]')?.value==='closed'&&location.hash.includes('estado=closed'));
      assert.equal(new URL(page.url()).searchParams.get('utm_source'),'qa-history','history: pushState dropped query string');
      await page.goBack({waitUntil:'domcontentloaded'}).catch(()=>null);
      await page.waitForFunction(()=>document.querySelector('[data-editoriales-status]')?.value==='open'&&location.hash.includes('estado=open'));
      assert.equal(await page.locator('[data-editoriales-search]').inputValue(),'Planeta','history: Back did not restore replaceState search');
      await page.goForward({waitUntil:'domcontentloaded'}).catch(()=>null);
      await page.waitForFunction(()=>document.querySelector('[data-editoriales-status]')?.value==='closed'&&location.hash.includes('estado=closed'));
      await page.locator('[data-editoriales-reset]').click();
      await page.waitForFunction(()=>location.hash==='');
      assert.equal(new URL(page.url()).searchParams.get('utm_source'),'qa-history','history: reset dropped query string');
      assert.equal(await page.locator('[data-editoriales-status]').inputValue(),'','history: reset did not clear status');
      assert.equal(await page.locator('[data-editoriales-country]').inputValue(),'','history: reset did not clear country');
      assert.equal(await page.locator('[data-editoriales-search]').inputValue(),'','history: reset did not clear search');
      const visibleAfterReset=await page.locator('[data-editorial-card]:not([hidden])').count();
      const total=await page.locator('[data-editorial-card]').count();
      assert.equal(visibleAfterReset,total,'history: reset did not restore all editorials');
    }catch(e){failures.push(String(e?.message||e))}finally{await page.close();await context.close()}
  }
}finally{await browser.close()}

assert.deepEqual(failures,[],failures.join('\n'));
console.log(`PASS production no-JS + history resilience: ${ROUTES.length} routes and Editoriales Back/Forward state`);
