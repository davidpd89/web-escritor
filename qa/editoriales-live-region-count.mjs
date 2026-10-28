import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE=process.env.QA_BASE_URL||process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try {
 const page=await browser.newPage();
 const response=await page.goto(`${BASE}/editoriales/`,{waitUntil:'domcontentloaded'});
 assert.ok(response?.ok(),'/editoriales/: error HTTP');
 const count=page.locator('[data-editoriales-count]');
 const search=page.locator('[data-editoriales-search]');
 for(const query of ['Minotauro','Nocturna','']) {
   await search.fill(query);
   await page.waitForFunction(()=>{
     const count=document.querySelector('[data-editoriales-count]');
     const n=[...document.querySelectorAll('[data-editorial-card]')].filter(el=>!el.hidden).length;
     return count?.textContent.trim()===`${n} ${n===1?'editorial':'editoriales'}`;
   });
   const state=await count.evaluate(el=>({role:el.getAttribute('role'),live:el.getAttribute('aria-live'),text:el.textContent.trim()}));
   assert.ok(state.role==='status'||['polite','assertive'].includes(state.live),`/editoriales/: contador no anunciable para búsqueda ${query}`);
   assert.equal(await count.count(),1,`/editoriales/: región de resultados duplicada para búsqueda ${query}`);
   assert.match(state.text,/^\d+ editoriales?$|^1 editorial$/,`/editoriales/: contador inválido ${state.text}`);
 }
} finally {await browser.close();}
