import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = (process.env.BASE_URL || process.env.QA_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const browser = await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});

try {
  for (const width of [320,390]) {
    const page = await browser.newPage({viewport:{width,height:900}});
    const route = '/mapa-del-sitio/';
    const response = await page.goto(BASE+route,{waitUntil:'load'});
    assert(response && response.ok(),`${route}: HTTP ${response?.status()}`);
    await page.locator('.findability-directory').waitFor({state:'visible'});
    await page.evaluate(()=>document.fonts.ready);
    const result = await page.evaluate(()=>{
      const selectors = '.findability-hero h1,.findability-hero__lead,.directory-group h2,.directory-list a,.directory-list small';
      const failures=[];
      for(const el of document.querySelectorAll(selectors)){
        const style=getComputedStyle(el);
        if(style.display==='none'||style.visibility==='hidden')continue;
        const rect=el.getBoundingClientRect();
        if(rect.width===0||rect.height===0)continue;
        if(rect.left < -1 || rect.right > innerWidth+1 || el.scrollWidth > el.clientWidth+2){
          failures.push({text:el.textContent.trim().slice(0,90),left:rect.left,right:rect.right,scrollWidth:el.scrollWidth,clientWidth:el.clientWidth});
        }
      }
      return {failures,documentWidth:document.documentElement.scrollWidth,viewportWidth:document.documentElement.clientWidth,count:document.querySelectorAll(selectors).length};
    });
    assert(result.count>20,`${route} ${width}px: corpus tipográfico insuficiente (${result.count})`);
    assert(result.documentWidth<=result.viewportWidth+1,`${route} ${width}px: documento ${result.documentWidth}px > viewport ${result.viewportWidth}px`);
    assert.deepEqual(result.failures,[],`${route} ${width}px: textos recortados: ${JSON.stringify(result.failures)}`);
    await page.close();
  }
} finally {await browser.close();}
console.log('PASS: findability typographic clipping');