import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=process.env.QA_BASE_URL||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try{
  for(const width of [320,390,768,1440]){
    const context=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce'});
    const page=await context.newPage();
    await page.goto(BASE+'/libros/#memoria-tierras-norte',{waitUntil:'load'});
    const section=page.locator('#memoria-tierras-norte');
    const heading=section.locator('h2');
    assert.equal(await section.count(),1);
    assert.equal(await heading.count(),1);
    await section.locator('img').evaluateAll(async images=>{
      await Promise.all(images.map(img=>img.decode().catch(()=>{})));
    });
    await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
    const geometry=await page.evaluate(()=>{
      const heading=document.querySelector('#memoria-tierras-norte h2');
      const rect=heading.getBoundingClientRect();
      const navs=[...document.querySelectorAll('.site-header,.section-context')];
      const bottom=Math.max(0,...navs.filter(el=>getComputedStyle(el).position==='fixed'||getComputedStyle(el).position==='sticky').map(el=>el.getBoundingClientRect().bottom));
      return {top:rect.top,bottom:rect.bottom,occlusion:bottom,viewport:innerHeight};
    });
    assert.ok(geometry.bottom>geometry.occlusion,`Encabezado oculto por navegación: ${JSON.stringify(geometry)}`);
    assert.ok(geometry.top<geometry.viewport,`Encabezado fuera de viewport: ${JSON.stringify(geometry)}`);
    await context.close();
  }
}finally{await browser.close();}
console.log('libros-anthology-anchor-lazy: OK');