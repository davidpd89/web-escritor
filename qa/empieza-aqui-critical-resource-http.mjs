import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const ORIGIN=(process.env.QA_ORIGIN||'http://127.0.0.1:4173').replace(/\/$/,'');
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try{
  const page=await browser.newPage();
  const errors=[];
  const inspected=[];
  page.on('requestfailed',req=>{
    const u=new URL(req.url());
    if(u.origin===ORIGIN&&/\.(?:css|js)$/i.test(u.pathname))errors.push(`${u.pathname}: ${req.failure()?.errorText}`);
  });
  page.on('response',res=>{
    const u=new URL(res.url());
    if(u.origin===ORIGIN&&/\.(?:css|js)$/i.test(u.pathname)){
      inspected.push(u.pathname);
      if(!res.ok())errors.push(`${u.pathname}: HTTP ${res.status()}`);
    }
  });
  const response=await page.goto(`${ORIGIN}/empieza-aqui/`,{waitUntil:'load'});
  assert(response?.ok(),`/empieza-aqui/: HTTP ${response?.status()}`);
  await page.locator('main .findability-entry').first().waitFor({state:'visible'});
  assert(inspected.some(p=>p.endsWith('.css')),'/empieza-aqui/: ninguna hoja CSS comprobada');
  assert(inspected.some(p=>p.endsWith('.js')),'/empieza-aqui/: ningún script comprobado');
  assert.deepEqual(errors,[],`/empieza-aqui/: recursos locales fallidos: ${errors.join('; ')}`);
  console.log(`Empieza aquí: ${inspected.length} respuestas CSS/JS comprobadas`);
}finally{await browser.close();}