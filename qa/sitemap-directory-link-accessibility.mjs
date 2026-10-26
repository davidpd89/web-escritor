import assert from 'node:assert/strict';
import {chromium} from 'playwright';
const BASE=(process.env.QA_ORIGIN||'http://127.0.0.1:4173').replace(/\/$/,'');
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try{
 for(const width of [320,390,768,1440]){
  const page=await browser.newPage({viewport:{width,height:900}});
  try{
   const response=await page.goto(BASE+'/mapa-del-sitio/',{waitUntil:'load'});
   assert(response?.ok(),`/mapa-del-sitio/ ${width}: HTTP ${response?.status()}`);
   const links=page.locator('main .directory-list a:visible');
   const count=await links.count();
   assert(count>0,`/mapa-del-sitio/ ${width}: ningún enlace visible`);
   for(let i=0;i<count;i++){
    const a=links.nth(i);
    const d=await a.evaluate(el=>{
     const r=el.getBoundingClientRect(),style=getComputedStyle(el);
     const labelledby=el.getAttribute('aria-labelledby');
     const referenced=labelledby?labelledby.split(/\s+/).map(id=>document.getElementById(id)?.textContent.trim()||'').join(' ').trim():'';
     return {name:(el.getAttribute('aria-label')||referenced||el.innerText||'').trim(),href:el.getAttribute('href'),width:r.width,height:r.height,tabIndex:el.tabIndex,visibility:style.visibility};
    });
    assert(d.name,`/mapa-del-sitio/ ${width}: enlace ${i} sin nombre accesible`);
    assert(d.href&&(/^(https?:\/\/|\/|#)/.test(d.href)),`/mapa-del-sitio/ ${width}: ${d.name} destino ${d.href}`);
    assert(d.width>0&&d.height>0,`/mapa-del-sitio/ ${width}: ${d.name} caja ${d.width}x${d.height}`);
    assert(d.tabIndex>=0,`/mapa-del-sitio/ ${width}: ${d.name} excluido del teclado`);
    assert.notEqual(d.visibility,'hidden',`/mapa-del-sitio/ ${width}: ${d.name} oculto`);
   }
  }finally{await page.close()}
 }
}finally{await browser.close()}
console.log('sitemap-directory-link-accessibility: OK');