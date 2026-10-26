import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base=process.env.QA_BASE_URL||process.env.BASE_URL;
assert.ok(base,'Configura QA_BASE_URL');
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try {
  for(const route of ['/lectores-beta/','/lectores-beta/enviar-manuscrito/']) {
    for(const css of ['v1-editorial.css','v1-beta-readers.css']) {
      const context=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844},serviceWorkers:'block'});
      const page=await context.newPage();
      let blocked=0;
      await page.route('**/*',async request=>{
        if(new URL(request.request().url()).pathname.endsWith('/'+css)) {
          blocked++;
          await request.abort();
        } else await request.continue();
      });
      const response=await page.goto(new URL(route,base).href,{waitUntil:'load'});
      assert.equal(response.status(),200,`${route}: HTTP ${response.status()}`);
      assert.ok(blocked>0,`${route}: no se interceptó ${css}`);
      const result=await page.evaluate(()=>{
        const main=document.querySelector('main');
        const h1=main?.querySelector('h1');
        const visible=el=>!!el && getComputedStyle(el).display!=='none' && getComputedStyle(el).visibility!=='hidden' && el.getBoundingClientRect().height>0;
        return {heading:visible(h1),main:visible(main),length:main?.innerText.length||0,links:[...main.querySelectorAll('a[href]')].filter(visible).length,overflow:document.documentElement.scrollWidth-innerWidth};
      });
      assert.ok(result.heading&&result.main,`${route} bloqueando ${css}: contenido oculto`);
      assert.ok(result.length>300,`${route} bloqueando ${css}: ${result.length} caracteres`);
      assert.ok(result.links>0,`${route} bloqueando ${css}: ningún enlace visible`);
      assert.ok(result.overflow<=8,`${route} bloqueando ${css}: desbordamiento ${result.overflow}px`);
      await context.close();
    }
  }
  console.log('beta-stylesheet-failure-geometry: OK');
}finally{await browser.close();}