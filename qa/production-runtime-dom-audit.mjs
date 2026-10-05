import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const O=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const S=(process.env.EXPECTED_RELEASE_SHA||'').trim();
const ROUTES=[
  '/',
  '/libros/',
  '/las-manecillas-del-recuerdo/',
  '/libros/samuel-entre-mundos/',
  '/cuaderno/',
  '/cuaderno/que-es-el-portal-fantasy/',
  '/herramientas/',
  '/herramientas/legibilidad/',
  '/asistente/',
  '/editoriales/',
  '/editoriales/editorial-espasa/',
  '/convocatorias-escritores/',
  '/metodologia-editorial/',
  '/prensa.html',
  '/eventos.html',
  '/ferias.html',
  '/mapa-del-sitio/',
  '/lectores-beta/',
];
const failures=[];

if(S){
  const r=await fetch(`${O}/_release/${S}.json?qa_runtime_dom=1`,{signal:AbortSignal.timeout(15000)});
  assert.equal(r.status,200,'release marker missing');
  assert.deepEqual(await r.json(),{schemaVersion:1,sha:S},'release marker mismatch');
}

const browser=await chromium.launch({headless:true});
try{
  for(const route of ROUTES){
    const context=await browser.newContext({viewport:{width:1280,height:900},reducedMotion:'reduce'});
    const page=await context.newPage();
    const pageErrors=[],badResponses=[];
    page.on('pageerror',e=>pageErrors.push(String(e)));
    page.on('response',r=>{
      try{
        const u=new URL(r.url());
        if(u.origin===O && r.status()>=400) badResponses.push(`${r.status()} ${u.pathname}`);
      }catch{}
    });
    await page.route(/(?:gc\.zgo\.at|goatcounter\.com|metricool\.com|clarity\.ms|c\.bing\.com)/,r=>r.abort());
    try{
      let response;
      for(let attempt=0;attempt<3;attempt++){
        response=await page.goto(`${O}${route}?qa_runtime_dom=${attempt}`,{waitUntil:'domcontentloaded',timeout:25000}).catch(()=>null);
        if(response && response.status()!==429 && (response.status()<500||response.status()>599)) break;
        await page.waitForTimeout(700*(attempt+1));
      }
      assert.equal(response?.status(),200,`${route}: navigation HTTP ${response?.status()}`);

      const enter=page.locator('[data-intro-enter]').first();
      if(await enter.count()){
        await page.evaluate(()=>document.querySelector('[data-intro-enter]')?.click());
        await page.waitForTimeout(500);
      }
      await page.waitForTimeout(450);

      const state=await page.evaluate(()=>{
        const els=[...document.querySelectorAll('*')];
        const ids=new Map();
        for(const el of els) if(el.id) ids.set(el.id,(ids.get(el.id)||0)+1);
        const duplicateIds=[...ids].filter(([,n])=>n>1).map(([id,n])=>({id,n}));

        const brokenAria=[];
        for(const el of els){
          for(const attr of ['aria-controls','aria-describedby','aria-labelledby','aria-owns']){
            const value=el.getAttribute?.(attr);
            if(!value) continue;
            for(const id of value.trim().split(/\s+/)){
              if(id && !document.getElementById(id)) brokenAria.push({tag:el.tagName.toLowerCase(),id:el.id||'',attr,target:id});
            }
          }
        }

        const brokenFragments=[];
        for(const a of document.querySelectorAll('a[href^="#"]')){
          const href=a.getAttribute('href');
          if(!href||href==='#') continue;
          let id='';
          try{id=decodeURIComponent(href.slice(1))}catch{id=href.slice(1)}
          if(id&&!document.getElementById(id)&&!document.querySelector(`[name="${CSS.escape(id)}"]`)) brokenFragments.push(href);
        }

        const invalidButtons=[...document.querySelectorAll('button')].filter(b=>!((b.textContent||'').trim()||b.getAttribute('aria-label')||b.getAttribute('title'))).map(b=>b.outerHTML.slice(0,180));
        const dialogs=[...document.querySelectorAll('dialog,[role="dialog"]')].filter(d=>!d.getAttribute('aria-label')&&!d.getAttribute('aria-labelledby')).map(d=>d.id||d.className||d.tagName);
        return {duplicateIds,brokenAria,brokenFragments:[...new Set(brokenFragments)],invalidButtons,dialogs};
      });

      assert.deepEqual(state.duplicateIds,[],`${route}: duplicate runtime IDs ${JSON.stringify(state.duplicateIds)}`);
      assert.deepEqual(state.brokenAria,[],`${route}: broken runtime ARIA refs ${JSON.stringify(state.brokenAria.slice(0,10))}`);
      assert.deepEqual(state.brokenFragments,[],`${route}: broken same-page fragments ${JSON.stringify(state.brokenFragments)}`);
      assert.deepEqual(state.invalidButtons,[],`${route}: unnamed buttons ${JSON.stringify(state.invalidButtons)}`);
      assert.deepEqual(state.dialogs,[],`${route}: unnamed dialogs ${JSON.stringify(state.dialogs)}`);
      assert.deepEqual(pageErrors,[],`${route}: page errors ${pageErrors.join(' | ')}`);
      assert.deepEqual([...new Set(badResponses)],[],`${route}: same-origin failed resources ${[...new Set(badResponses)].join(', ')}`);
      console.log('PASS runtime DOM '+route);
    }catch(e){
      failures.push(e.message);
      console.error('FAIL runtime DOM '+route+': '+e.message);
    }finally{
      await context.close();
    }
  }
}finally{
  await browser.close();
}
assert.deepEqual(failures,[],failures.join('\n'));
console.log(`PASS production runtime DOM: ${ROUTES.length} routes`);
