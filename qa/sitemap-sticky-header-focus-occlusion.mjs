import assert from 'node:assert/strict';
import {chromium} from 'playwright';
const BASE=(process.env.QA_ORIGIN||'http://127.0.0.1:4173').replace(/\/$/,'');
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try{
 for(const width of [320,390,768,1440]){
  const page=await browser.newPage({viewport:{width,height:900},reducedMotion:'reduce'});
  try{
   const response=await page.goto(BASE+'/mapa-del-sitio/',{waitUntil:'load'});
   assert(response?.ok(),`/mapa-del-sitio/ ${width}: HTTP ${response?.status()}`);
   const links=page.locator('main .directory-list a:visible');
   const count=await links.count();
   assert(count>0,`/mapa-del-sitio/ ${width}: sin enlaces`);
   for(let i=0;i<count;i++){
    const link=links.nth(i);
    await link.focus();
    await link.evaluate(el=>el.scrollIntoView({block:'center',inline:'nearest',behavior:'instant'}));
    const d=await link.evaluate(el=>{
     const r=el.getBoundingClientRect(),h=document.querySelector('.site-header')?.getBoundingClientRect();
     const headerBottom=h&&h.bottom>0&&h.top<innerHeight?h.bottom:0;
     return {name:el.textContent.trim(),top:r.top,bottom:r.bottom,left:r.left,right:r.right,headerBottom,focused:document.activeElement===el};
    });
    assert(d.focused,`/mapa-del-sitio/ ${width}: ${d.name} perdió foco`);
    assert(d.bottom>Math.max(0,d.headerBottom)&&d.top<900,`/mapa-del-sitio/ ${width}: ${d.name} oculto por cabecera ${JSON.stringify(d)}`);
    assert(d.left>=-1&&d.right<=width+1,`/mapa-del-sitio/ ${width}: ${d.name} fuera del ancho ${JSON.stringify(d)}`);
   }
  }finally{await page.close()}
 }
}finally{await browser.close()}
console.log('sitemap-sticky-header-focus-occlusion: OK');