import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=(process.env.QA_ORIGIN||process.env.SITE_BASE_URL||'http://127.0.0.1:4173').replace(/\/$/,'');
const routes=['/libros/','/libros/samuel-entre-mundos/','/las-manecillas-del-recuerdo/'];
const browser=await chromium.launch({headless:true});
try {
  for(const width of [320,360,390,600,768,1280]) {
    const page=await browser.newPage({viewport:{width,height:900},reducedMotion:'reduce'});
    for(const route of routes) {
      const response=await page.goto(BASE+route,{waitUntil:'domcontentloaded'});
      assert.equal(response?.status(),200,`${route} ${width}px: respuesta HTTP incorrecta`);
      await page.evaluate(()=>document.fonts.ready);
      const images=page.locator('main img');
      for(let i=0;i<await images.count();i++) {
        const img=images.nth(i);
        await img.scrollIntoViewIfNeeded().catch(()=>{});
        const geometry=await img.evaluate(el=>{
          const s=getComputedStyle(el),r=el.getBoundingClientRect();
          return {src:el.currentSrc||el.src,left:r.left,right:r.right,width:r.width,visible:s.display!=='none'&&s.visibility!=='hidden'&&r.width>0};
        });
        if(!geometry.visible) continue;
        assert.ok(geometry.left>=-1&&geometry.right<=width+1,`${route} ${width}px: imagen ${geometry.src} fuera de ventana: ${JSON.stringify(geometry)}`);
      }
      const overflow=await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth);
      assert.ok(overflow<=1,`${route} ${width}px: desbordamiento horizontal ${overflow}px`);
    }
    await page.close();
  }
} finally {await browser.close();}
console.log('PASS media-viewport-containment');