import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const ORIGIN=(process.env.QA_ORIGIN||'http://127.0.0.1:4173').replace(/\/$/,'');
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try{
  const page=await browser.newPage();
  const response=await page.goto(`${ORIGIN}/empieza-aqui/`,{waitUntil:'load'});
  assert(response?.ok(),`/empieza-aqui/: HTTP ${response?.status()}`);
  const entries=await page.evaluate(()=>performance.getEntriesByType('resource').filter(e=>{
    const u=new URL(e.name);
    return u.origin===location.origin&&/\.(css|js)$/i.test(u.pathname);
  }).map(e=>({url:new URL(e.name).pathname+new URL(e.name).search,initiator:e.initiatorType})));
  assert(entries.length>0,'/empieza-aqui/: no se registraron recursos CSS/JS');
  const counts=new Map();
  for(const e of entries){
    if(e.initiator==='link'||e.initiator==='script')counts.set(e.url,(counts.get(e.url)||0)+1);
  }
  const duplicates=[...counts].filter(([,n])=>n>1);
  assert.deepEqual(duplicates,[],`/empieza-aqui/: recursos CSS/JS repetidos: ${JSON.stringify(duplicates)}`);
  console.log(`Empieza aquí: ${counts.size} recursos CSS/JS sin duplicación inicial`);
}finally{await browser.close();}