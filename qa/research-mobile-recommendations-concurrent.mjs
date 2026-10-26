import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=(process.env.SITE_BASE_URL||'http://127.0.0.1:8000').replace(/\/$/,'');
const browser=await chromium.launch({headless:true});
try {
  await Promise.all(Array.from({length:9},async(_,i)=>{
    const width=[320,360,390][i%3];
    const context=await browser.newContext({viewport:{width,height:740},hasTouch:true,isMobile:true,serviceWorkers:'block'});
    const page=await context.newPage();
    await page.route('**/*',r=>new URL(r.request().url()).origin===new URL(BASE).origin?r.continue():r.abort());
    try {
      const response=await page.goto(BASE+'/recomendaciones/',{waitUntil:'load',timeout:30000});
      assert.equal(response?.status(),200,`/recomendaciones/ ${width}px visita ${i}: HTTP ${response?.status()}`);
      const result=await page.evaluate(()=>{
        const links=[...document.querySelectorAll('main a[href]')].filter(a=>{
          const r=a.getBoundingClientRect(),s=getComputedStyle(a);
          return r.width>0&&r.height>0&&s.visibility!=='hidden'&&s.display!=='none'&&a.href.startsWith(location.origin+'/');
        });
        return {text:document.querySelector('main')?.innerText.trim().length||0,links:links.length,overflow:document.documentElement.scrollWidth-document.documentElement.clientWidth};
      });
      assert.ok(result.text>100,`/recomendaciones/ ${width}px visita ${i}: contenido vacío`);
      assert.ok(result.links>0,`/recomendaciones/ ${width}px visita ${i}: sin enlaces internos visibles`);
      assert.ok(result.overflow<=1,`/recomendaciones/ ${width}px visita ${i}: desbordamiento ${result.overflow}px`);
    } finally {await context.close();}
  }));
  console.log('PASS recommendations concurrent mobile navigation');
} finally {await browser.close();}
