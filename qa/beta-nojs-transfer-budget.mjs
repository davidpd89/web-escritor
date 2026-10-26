import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = process.env.QA_BASE_URL || process.env.BASE_URL;
assert.ok(base,'Configura QA_BASE_URL');
const origin = new URL(base).origin;
const browser = await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try {
  for(const route of ['/lectores-beta/','/lectores-beta/enviar-manuscrito/']) {
    const context = await browser.newContext({javaScriptEnabled:false,serviceWorkers:'block'});
    const page = await context.newPage();
    const resources = [];
    page.on('response',async response=>{
      if(new URL(response.url()).origin!==origin)return;
      const request=response.request();
      if(request.method()!=='GET')return;
      try {
        const body=await response.body();
        resources.push({url:response.url(),bytes:body.length,status:response.status()});
      } catch(e) {resources.push({url:response.url(),bytes:0,error:String(e)});}
    });
    const response=await page.goto(new URL(route,base).href,{waitUntil:'load'});
    assert.equal(response.status(),200,`${route}: HTTP ${response.status()}`);
    await page.waitForLoadState('networkidle');
    assert.ok(resources.length>0,`${route}: no se observaron recursos`);
    const failures=resources.filter(r=>r.error || r.status>=400);
    assert.deepEqual(failures,[],`${route}: recursos locales fallidos: ${JSON.stringify(failures)}`);
    const total=resources.reduce((sum,r)=>sum+r.bytes,0);
    assert.ok(total<=512*1024,`${route}: ${total} bytes, máximo 524288`);
    assert.ok(resources.length<=35,`${route}: ${resources.length} peticiones, máximo 35`);
    const counts=new Map();
    for(const r of resources)counts.set(r.url,(counts.get(r.url)||0)+1);
    const duplicates=[...counts].filter(([,n])=>n>1);
    assert.deepEqual(duplicates,[],`${route}: descargas duplicadas ${JSON.stringify(duplicates)}`);
    await context.close();
  }
  console.log('beta-nojs-transfer-budget: OK');
}finally{await browser.close();}