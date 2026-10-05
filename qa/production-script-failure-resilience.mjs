import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { assertProductionRelease } from './production-release-marker.mjs';

const O=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const S=(process.env.EXPECTED_RELEASE_SHA||'').trim();

const CASES=[
  {
    route:'/editoriales/',
    block:/\/assets\/(?:v1-shell|editoriales)\.js(?:\?|$)/,
    required:'[data-editorial-card]',
    min:100,
  },
  {
    route:'/convocatorias-escritores/',
    block:/\/assets\/(?:v1-shell|radar-convocatorias)\.js(?:\?|$)/,
    required:'[data-radar-item]',
    min:1,
  },
  {
    route:'/metodologia-editorial/',
    block:/\/assets\/v1-shell\.js(?:\?|$)/,
    required:'main a[href]',
    min:3,
  },
  {
    route:'/mapa-del-sitio/',
    block:/\/assets\/v1-shell\.js(?:\?|$)/,
    required:'main a[href]',
    min:10,
  },
];

await assertProductionRelease({origin:O,sha:S,label:'script-failure-resilience'});

const browser=await chromium.launch({headless:true});
const failures=[];
try{
  for(const c of CASES){
    const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,reducedMotion:'reduce'});
    const page=await context.newPage();
    try{
      await page.route(c.block,route=>route.abort('failed'));
      const response=await page.goto(O+c.route+'?qa_script_failure=1',{waitUntil:'domcontentloaded',timeout:25000});
      assert.equal(response?.status(),200,c.route+': HTTP '+response?.status());

      const state=await page.evaluate(selector=>{
        const main=document.querySelector('main');
        const h1=document.querySelector('h1');
        const style=main?getComputedStyle(main):null;
        return {
          h1:(h1?.textContent||'').trim(),
          mainText:(main?.innerText||'').trim(),
          mainVisible:Boolean(main&&style&&style.display!=='none'&&style.visibility!=='hidden'&&Number(style.opacity)!==0&&main.getBoundingClientRect().height>40),
          matches:document.querySelectorAll(selector).length,
          links:[...document.querySelectorAll('main a[href]')].filter(a=>{
            const s=getComputedStyle(a);
            return s.display!=='none'&&s.visibility!=='hidden';
          }).length,
        };
      },c.required);

      assert.ok(state.h1,c.route+': H1 disappeared when script failed');
      assert.equal(state.mainVisible,true,c.route+': main content became hidden when script failed');
      assert.ok(state.mainText.length>120,c.route+': server-rendered content became suspiciously empty');
      assert.ok(state.matches>=c.min,c.route+': required fallback content '+state.matches+' < '+c.min);
      assert.ok(state.links>=2,c.route+': no usable main links remain after script failure');
    }catch(e){
      failures.push(String(e?.message||e));
    }finally{
      await page.close();
      await context.close();
    }
  }
}finally{
  await browser.close();
}

assert.deepEqual(failures,[],failures.join('\n'));
console.log('PASS production script-failure resilience: '+CASES.length+' server-rendered routes survive failed JS delivery');
