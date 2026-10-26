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
   assert(count>0,`/mapa-del-sitio/ ${width}: directorio vacío`);
   for(let i=0;i<count;i++){
    const link=links.nth(i);
    await link.focus();
    const data=await link.evaluate(el=>{
     const s=getComputedStyle(el),r=el.getBoundingClientRect();
     return {focused:document.activeElement===el,name:el.getAttribute('aria-label')||el.textContent.trim(),left:r.left,right:r.right,width:r.width,height:r.height,outline:s.outlineStyle,outlineWidth:parseFloat(s.outlineWidth),boxShadow:s.boxShadow,border:s.borderStyle,background:s.backgroundColor};
    });
    assert(data.focused,`/mapa-del-sitio/ ${width}: enlace ${i} no recibe foco`);
    assert(data.name,`/mapa-del-sitio/ ${width}: enlace ${i} sin nombre`);
    assert(data.width>0&&data.height>0&&data.left>=-1&&data.right<=width+1,`/mapa-del-sitio/ ${width}: ${data.name} fuera de viewport ${JSON.stringify(data)}`);
    assert((data.outline!=='none'&&data.outlineWidth>0)||data.boxShadow!=='none',`/mapa-del-sitio/ ${width}: ${data.name} sin indicador de foco computado ${JSON.stringify(data)}`);
   }
  }finally{await page.close()}
 }
}finally{await browser.close()}
console.log('sitemap-keyboard-focus-visibility: OK');