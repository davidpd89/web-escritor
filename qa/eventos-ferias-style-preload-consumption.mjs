import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try {
  for(const route of ['/eventos.html','/ferias.html']) {
    const context=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'});
    const page=await context.newPage();
    const requests=[];
    page.on('request',r=>{if(new URL(r.url()).origin===new URL(BASE).origin&&new URL(r.url()).pathname.endsWith('.css')) requests.push(r.url());});
    const response=await page.goto(BASE+route,{waitUntil:'networkidle'});
    assert.ok(response?.ok(),`${route}: HTTP ${response?.status()}`);
    const state=await page.evaluate(()=>({preloads:[...document.querySelectorAll('link[rel="preload"][as="style"]')].map(x=>x.href),used:[...document.styleSheets].map(x=>x.href).filter(Boolean),entries:performance.getEntriesByType('resource').filter(x=>x.initiatorType==='css'||x.name.includes('.css')).map(x=>x.name)}));
    assert.ok(state.preloads.length>0,`${route}: no se localizaron precargas CSS`);
    for(const url of state.preloads) {
      assert.ok(requests.includes(url),`${route}: precarga CSS no solicitada: ${url}`);
      const count=requests.filter(x=>x===url).length;
      assert.ok(count<=1,`${route}: ${url} solicitada ${count} veces`);
    }
    const unused=state.preloads.filter(url=>!state.used.includes(url)&&!state.entries.some(entry=>entry===url&&state.used.length===0));
    if(unused.length) console.log(`${route}: precargas indirectas que requieren comprobación de @import: ${unused.join(', ')}`);
    await context.close();
  }
} finally {await browser.close();}
