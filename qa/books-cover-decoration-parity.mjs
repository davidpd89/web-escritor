import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=(process.env.QA_ORIGIN||process.env.SITE_BASE_URL||'http://127.0.0.1:4173').replace(/\/$/,'');
const browser=await chromium.launch({headless:true});
try {
  for(const width of [360,390,768,900,901,1280]) {
    const page=await browser.newPage({viewport:{width,height:900},reducedMotion:'reduce'});
    const response=await page.goto(BASE+'/libros/',{waitUntil:'domcontentloaded'});
    assert.equal(response?.status(),200,`/libros/ ${width}px: HTTP incorrecto`);
    await page.evaluate(()=>document.fonts.ready);
    const items=page.locator('main[data-family="books-index"] .books-stage__media');
    const count=await items.count();
    assert.ok(count>=2,`/libros/ ${width}px: faltan componentes de portada para comparar`);
    const values=[];
    for(let i=0;i<count;i++) {
      const item=items.nth(i);
      await item.scrollIntoViewIfNeeded();
      const value=await item.evaluate(el=>{
        const before=getComputedStyle(el,'::before');
        const after=getComputedStyle(el,'::after');
        const img=el.querySelector('img');
        const r=img?.getBoundingClientRect();
        return {before:before.backgroundImage,after:after.backgroundImage,width:r?.width||0,height:r?.height||0};
      });
      assert.match(value.before,/corner-bracket-blue-gold\.svg/,`/libros/ ${width}px: portada ${i+1} sin esquina inicial`);
      assert.match(value.after,/corner-bracket-blue-gold\.svg/,`/libros/ ${width}px: portada ${i+1} sin esquina final`);
      assert.ok(value.width>=80&&value.height>=120,`/libros/ ${width}px: portada ${i+1} demasiado pequeña ${value.width}x${value.height}`);
      values.push(value);
    }
    for(const [i,value] of values.entries()) {
      assert.equal(value.before,values[0].before,`/libros/ ${width}px: decoración inicial distinta en portada ${i+1}`);
      assert.equal(value.after,values[0].after,`/libros/ ${width}px: decoración final distinta en portada ${i+1}`);
    }
    await page.close();
  }
} finally {await browser.close();}
console.log('PASS books-cover-decoration-parity');