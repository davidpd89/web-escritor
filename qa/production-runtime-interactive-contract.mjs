import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { assertProductionRelease } from './production-release-marker.mjs';

const O=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const S=(process.env.EXPECTED_RELEASE_SHA||'').trim();
const ROUTES=[
  '/', '/libros/', '/las-manecillas-del-recuerdo/', '/libros/samuel-entre-mundos/',
  '/cuaderno/', '/herramientas/', '/asistente/', '/editoriales/',
  '/editoriales/editorial-espasa/', '/convocatorias-escritores/', '/metodologia-editorial/',
  '/prensa.html', '/eventos.html', '/ferias.html', '/mapa-del-sitio/', '/lectores-beta/'
];

await assertProductionRelease({origin:O,sha:S,label:'runtime-interactive'});

const browser=await chromium.launch({headless:true});
const failures=[];
try{
  for(const route of ROUTES){
    const context=await browser.newContext({viewport:{width:1280,height:900},reducedMotion:'reduce'});
    const page=await context.newPage();
    await page.route(/(?:gc\.zgo\.at|goatcounter\.com|metricool\.com|clarity\.ms|c\.bing\.com)/,r=>r.abort());
    try{
      const r=await page.goto(`${O}${route}?qa_runtime_interactive=${encodeURIComponent(S||'live')}`,{waitUntil:'domcontentloaded',timeout:25000});
      assert.equal(r?.status(),200,`${route}: HTTP ${r?.status()}`);
      const enter=page.locator('[data-intro-enter]').first();
      if(await enter.count()) await page.evaluate(()=>document.querySelector('[data-intro-enter]')?.click());
      await page.waitForTimeout(300);
      const state=await page.evaluate(()=>{
        const badHref=[...document.querySelectorAll('a[href]')].filter(a=>/^(?:null|undefined|\[object object\])$/i.test((a.getAttribute('href')||'').trim())).map(a=>a.outerHTML.slice(0,220));
        const unsafeBlank=[...document.querySelectorAll('a[target="_blank"]')].filter(a=>!new Set((a.getAttribute('rel')||'').toLowerCase().split(/\s+/)).has('noopener')).map(a=>a.outerHTML.slice(0,220));
        const affiliate=[...document.querySelectorAll('a[href*="amzn.to"],a[href*="amazon."]')].filter(a=>{
          const rel=new Set((a.getAttribute('rel')||'').toLowerCase().split(/\s+/));
          return !rel.has('sponsored')&&!rel.has('nofollow');
        }).map(a=>a.outerHTML.slice(0,220));
        const imageAlt=[...document.querySelectorAll('img')].filter(img=>!img.hasAttribute('alt')).map(img=>img.outerHTML.slice(0,220));
        const iframeTitle=[...document.querySelectorAll('iframe')].filter(f=>!(f.getAttribute('title')||'').trim()).map(f=>f.outerHTML.slice(0,220));
        const unnamedControls=[...document.querySelectorAll('input:not([type="hidden"]),select,textarea')].filter(el=>{
          const labelled=(el.getAttribute('aria-label')||'').trim()||(el.getAttribute('aria-labelledby')||'').trim();
          const labels=el.labels?.length||0;
          return !labelled&&!labels;
        }).map(el=>el.outerHTML.slice(0,220));
        return {badHref,unsafeBlank,affiliate,imageAlt,iframeTitle,unnamedControls};
      });
      for(const [kind,items] of Object.entries(state)) assert.deepEqual(items,[],`${route}: ${kind} ${JSON.stringify(items.slice(0,8))}`);
    }catch(e){failures.push(String(e?.message||e))}finally{await page.close();await context.close()}
  }
}finally{await browser.close()}

assert.deepEqual(failures,[],failures.join('\n'));
console.log(`PASS production runtime interactive contract: ${ROUTES.length} representative routes`);
