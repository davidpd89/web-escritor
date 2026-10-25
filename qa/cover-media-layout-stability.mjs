import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=(process.env.QA_ORIGIN||process.env.SITE_BASE_URL||'http://127.0.0.1:4173').replace(/\/$/,'');
const routes=[
  ['/libros/','main[data-family="books-index"] .books-stage__media img'],
  ['/libros/samuel-entre-mundos/','.samuel-object img'],
  ['/las-manecillas-del-recuerdo/','.book-cover img']
];
const browser=await chromium.launch({headless:true});
try {
  for(const width of [360,390,768,1280]) {
    for(const [route,selector] of routes) {
      const page=await browser.newPage({viewport:{width,height:900},reducedMotion:'reduce'});
      await page.route(/\.(?:avif|webp|png|jpe?g)(?:\?.*)?$/i,async request=>{
        if(request.request().resourceType()!=='image') return request.continue();
        await new Promise(resolve=>setTimeout(resolve,150));
        await request.continue();
      });
      const response=await page.goto(BASE+route,{waitUntil:'domcontentloaded'});
      assert.equal(response?.status(),200,`${route} ${width}px: HTTP incorrecto`);
      const imgs=page.locator(selector);
      const count=await imgs.count();
      assert.ok(count>0,`${route} ${width}px: no hay cubiertas`);
      await page.evaluate(()=>document.fonts.ready);
      for(let i=0;i<count;i++) {
        const img=imgs.nth(i);
        await img.scrollIntoViewIfNeeded();
        const before=await img.evaluate(el=>{const r=el.getBoundingClientRect();return {width:r.width,height:r.height};});
        await img.evaluate(async el=>{if(!el.complete) await new Promise(resolve=>{el.addEventListener('load',resolve,{once:true});el.addEventListener('error',resolve,{once:true});});});
        const after=await img.evaluate(el=>{const r=el.getBoundingClientRect();return {width:r.width,height:r.height,loaded:el.naturalWidth>0};});
        assert.ok(after.loaded,`${route} ${width}px: cubierta ${i+1} no cargada`);
        assert.ok(before.width>0&&before.height>0,`${route} ${width}px: cubierta ${i+1} sin espacio reservado`);
        assert.ok(Math.abs(before.height-after.height)<=2,`${route} ${width}px: cubierta ${i+1} cambia altura ${before.height} -> ${after.height}`);
      }
      await page.close();
    }
  }
} finally {await browser.close();}
console.log('PASS cover-media-layout-stability');