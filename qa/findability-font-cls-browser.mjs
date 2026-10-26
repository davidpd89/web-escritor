import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE=(process.env.BASE_URL||process.env.QA_BASE_URL||'http://127.0.0.1:8000').replace(/\/$/,'');
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try {
  for(const width of [390,1440]){
    const context=await browser.newContext({viewport:{width,height:900},serviceWorkers:'block'});
    const page=await context.newPage();
    await page.addInitScript(()=>{
      window.__fontCLS={score:0,entries:0};
      new PerformanceObserver(list=>{
        for(const entry of list.getEntries()){
          if(!entry.hadRecentInput){window.__fontCLS.score+=entry.value;window.__fontCLS.entries++;}
        }
      }).observe({type:'layout-shift',buffered:true});
    });
    const failed=[];
    page.on('requestfailed',r=>{if(/\.(woff2?|css)(\?|$)/i.test(r.url()))failed.push(r.url());});
    const response=await page.goto(BASE+'/mapa-del-sitio/',{waitUntil:'load'});
    assert(response?.ok(),`/mapa-del-sitio/ ${width}px: HTTP ${response?.status()}`);
    await page.locator('.findability-directory').waitFor({state:'visible'});
    await page.evaluate(async()=>{await document.fonts.ready;await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));});
    const metrics=await page.evaluate(()=>({cls:window.__fontCLS.score,entries:window.__fontCLS.entries,fonts:document.fonts.status}));
    assert.equal(metrics.fonts,'loaded',`/mapa-del-sitio/ ${width}px: fuentes pendientes`);
    assert.deepEqual(failed,[],`/mapa-del-sitio/ ${width}px: recursos tipográficos fallidos: ${failed}`);
    assert(metrics.cls<0.1,`/mapa-del-sitio/ ${width}px: CLS=${metrics.cls}, eventos=${metrics.entries}, máximo permitido <0.1`);
    await context.close();
  }
} finally {await browser.close();}
console.log('PASS: findability font CLS');