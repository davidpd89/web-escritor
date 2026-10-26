import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base=process.env.QA_BASE_URL||process.env.BASE_URL;
assert.ok(base,'Configura QA_BASE_URL');
const origin=new URL(base).origin;
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try {
  for(const route of ['/lectores-beta/','/lectores-beta/enviar-manuscrito/']) {
    const context=await browser.newContext({serviceWorkers:'block'});
    const page=await context.newPage();
    const errors=[];
    const scripts=[];
    await page.route('**/*',async r=>{
      if(new URL(r.request().url()).origin!==origin) return r.abort();
      await r.continue();
    });
    page.on('pageerror',e=>errors.push(`pageerror: ${e.message}`));
    page.on('console',m=>{
      if(m.type()==='error')errors.push(`console: ${m.text()}`);
    });
    page.on('requestfailed',r=>{
      if(new URL(r.url()).origin===origin)errors.push(`requestfailed: ${r.url()} ${r.failure()?.errorText}`);
    });
    page.on('response',r=>{
      if(new URL(r.url()).origin===origin && new URL(r.url()).pathname.endsWith('.js'))scripts.push({url:r.url(),status:r.status()});
    });
    const response=await page.goto(new URL(route,base).href,{waitUntil:'load'});
    assert.equal(response.status(),200,`${route}: HTTP ${response.status()}`);
    await page.waitForLoadState('networkidle');
    assert.ok(scripts.length>0,`${route}: no se observaron scripts locales`);
    assert.deepEqual(scripts.filter(s=>s.status>=400),[],`${route}: scripts HTTP fallidos`);
    assert.deepEqual(errors,[],`${route}: errores de ejecución: ${JSON.stringify(errors)}`);
    assert.equal(await page.locator('main h1:visible').count(),1,`${route}: contenido principal no disponible`);
    await context.close();
  }
  console.log('beta-runtime-script-observation: OK');
}finally{await browser.close();}