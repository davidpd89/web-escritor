import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE=(process.env.SITE_BASE_URL||'http://127.0.0.1:8000').replace(/\/$/,'');
const browser=await chromium.launch({headless:true});
try {
  await Promise.all(Array.from({length:10},async(_,i)=>{
    const width=[320,375,390][i%3];
    const context=await browser.newContext({viewport:{width,height:720},serviceWorkers:'block'});
    const page=await context.newPage();
    const failures=[];
    let checked=0;
    await page.route('**/*',route=>new URL(route.request().url()).origin===new URL(BASE).origin?route.continue():route.abort());
    page.on('response',response=>{
      const url=new URL(response.url());
      if(url.origin===new URL(BASE).origin && /\.(css|js)$/.test(url.pathname)) {
        checked++;
        if(response.status()!==200) failures.push(`${url.pathname}: HTTP ${response.status()}`);
      }
    });
    try {
      const response=await page.goto(BASE+'/herramientas/',{waitUntil:'networkidle',timeout:30000});
      assert.equal(response?.status(),200,`/herramientas/ ${width}px visita ${i}: HTTP ${response?.status()}`);
      assert.ok(checked>0,`/herramientas/ ${width}px visita ${i}: ningún CSS/JS comprobado`);
      assert.deepEqual(failures,[],`/herramientas/ ${width}px visita ${i}: ${failures.join('; ')}`);
      const state=await page.evaluate(()=>({main:document.querySelector('main')?.innerText.trim().length||0,overflow:document.documentElement.scrollWidth-document.documentElement.clientWidth}));
      assert.ok(state.main>100,`/herramientas/ ${width}px visita ${i}: contenido principal vacío`);
      assert.ok(state.overflow<=1,`/herramientas/ ${width}px visita ${i}: desbordamiento ${state.overflow}px`);
    } finally {await context.close();}
  }));
  console.log('PASS tools concurrent resources');
} finally {await browser.close();}
