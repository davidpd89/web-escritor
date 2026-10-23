import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const O=(process.env.QA_ORIGIN||'http://127.0.0.1:4173').replace(/\/$/,'');
const routes=['/','/libros/','/cuaderno/','/editoriales/','/herramientas/','/convocatorias-escritores/','/asistente/','/mapa-del-sitio/'];
const browser=await chromium.launch({headless:true});
const errors=[];
try{
  const context=await browser.newContext({viewport:{width:390,height:844}});
  await context.route('**/*',r=>{const u=new URL(r.request().url());if(u.origin!==O)return r.abort();if(/\/(?:assets\/v1-shell|script)\.js$/.test(u.pathname))return r.abort();return r.continue();});
  const page=await context.newPage();
  for(const route of routes){
    try{
      await page.goto(O+route,{waitUntil:'load'});
      const s=await page.evaluate(()=>({h1:document.querySelector('main h1')?.innerText.trim(),links:[...document.querySelectorAll('main a[href^="/"]')].filter(a=>a.getClientRects().length&&getComputedStyle(a).visibility!=='hidden').length,home:!!document.querySelector('header a[href="/"]'),sitemap:!!document.querySelector('header a[href="/mapa-del-sitio/"]')}));
      assert.ok(s.h1&&s.links>0&&s.home&&s.sitemap,route+': recuperación incompleta '+JSON.stringify(s));
    }catch(e){errors.push(e.message);}
  }
  await context.close();
}finally{await browser.close();}
assert.deepEqual(errors,[],errors.join('\n'));
console.log('PASS shell script failure sitewide');