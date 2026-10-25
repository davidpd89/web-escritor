import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = (process.env.QA_ORIGIN || process.env.SITE_BASE_URL || 'http://127.0.0.1:4173').replace(/\/$/, '');
const routes = [
  ['/libros/', 'main[data-family="books-index"] .books-stage__media img'],
  ['/libros/samuel-entre-mundos/', '.samuel-object img'],
  ['/las-manecillas-del-recuerdo/', '.book-cover img']
];
const browser = await chromium.launch({headless:true});
try {
  for (const width of [360,390,768,1280]) {
    const page = await browser.newPage({viewport:{width,height:900},reducedMotion:'reduce'});
    for (const [route,selector] of routes) {
      const response = await page.goto(BASE+route,{waitUntil:'domcontentloaded'});
      assert.equal(response?.status(),200,`${route} ${width}px: HTTP ${response?.status()}`);
      await page.evaluate(()=>document.fonts.ready);
      const images = page.locator(selector);
      const count = await images.count();
      assert.ok(count>0,`${route} ${width}px: ninguna cubierta encontrada`);
      for (let i=0;i<count;i++) {
        const image = images.nth(i);
        await image.scrollIntoViewIfNeeded();
        await image.evaluate(async el=>{if(!el.complete) await new Promise(resolve=>{el.addEventListener('load',resolve,{once:true});el.addEventListener('error',resolve,{once:true});});});
        const result = await image.evaluate(el=>{
          const r=el.getBoundingClientRect();
          return {src:el.currentSrc,width:r.width,height:r.height,nw:el.naturalWidth,nh:el.naturalHeight};
        });
        assert.ok(result.nw>0&&result.nh>0,`${route} ${width}px: cubierta ${result.src} sin decodificar`);
        assert.ok(result.width>0&&result.height>0,`${route} ${width}px: cubierta ${result.src} sin caja`);
        const deviation=Math.abs(result.width/result.height-result.nw/result.nh)/(result.nw/result.nh);
        assert.ok(deviation<=0.02,`${route} ${width}px: ${result.src} deformada ${(deviation*100).toFixed(2)}%`);
      }
    }
    await page.close();
  }
} finally {await browser.close();}
console.log('PASS media-cover-aspect-parity');