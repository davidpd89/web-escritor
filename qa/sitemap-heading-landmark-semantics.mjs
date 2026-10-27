import assert from 'node:assert/strict';
import {chromium} from 'playwright';
const BASE=(process.env.QA_ORIGIN||'http://127.0.0.1:4173').replace(/\/$/,'');
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try{
 for(const width of [320,768,1440]){
  const page=await browser.newPage({viewport:{width,height:900}});
  try{
   const response=await page.goto(BASE+'/mapa-del-sitio/',{waitUntil:'load'});
   assert(response?.ok(),`/mapa-del-sitio/ ${width}: HTTP ${response?.status()}`);
   const result=await page.evaluate(()=>{
    const main=document.querySelector('main');
    const sections=[...document.querySelectorAll('main .directory-group')];
    return {mains:document.querySelectorAll('main').length,h1:[...document.querySelectorAll('main h1')].filter(e=>e.getClientRects().length).map(e=>e.textContent.trim()),sections:sections.map(s=>({id:s.id,headings:[...s.querySelectorAll('h2')].map(h=>h.textContent.trim()),links:[...s.querySelectorAll('a[href]')].filter(a=>a.getClientRects().length&&a.textContent.trim()).length})),mainPresent:!!main};
   });
   assert.equal(result.mains,1,`/mapa-del-sitio/ ${width}: ${result.mains} regiones main`);
   assert.equal(result.h1.length,1,`/mapa-del-sitio/ ${width}: H1 visibles ${JSON.stringify(result.h1)}`);
   assert(result.h1[0],`/mapa-del-sitio/ ${width}: H1 vacío`);
   assert(result.sections.length>=2,`/mapa-del-sitio/ ${width}: faltan secciones del directorio`);
   for(const s of result.sections){
    assert(s.id,`/mapa-del-sitio/ ${width}: sección sin identificador`);
    assert.equal(s.headings.length,1,`/mapa-del-sitio/ ${width}: sección ${s.id} con ${s.headings.length} H2`);
    assert(s.headings[0],`/mapa-del-sitio/ ${width}: encabezado vacío en ${s.id}`);
    assert(s.links>0,`/mapa-del-sitio/ ${width}: sección ${s.id} sin enlaces textuales`);
   }
  }finally{await page.close()}
 }
}finally{await browser.close()}
console.log('sitemap-heading-landmark-semantics: OK');