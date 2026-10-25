import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true});
try {
  const context=await browser.newContext({viewport:{width:1024,height:900}});
  await context.route('**/*',r=>new URL(r.request().url()).origin===new URL(BASE).origin?r.continue():r.abort());
  try {
    for(const route of ['/eventos.html','/ferias.html']) {
      const page=await context.newPage();
      await page.goto(BASE+route,{waitUntil:'domcontentloaded'});
      const images=page.locator('main figure img');
      assert.ok(await images.count()>0,route+': sin fotos');
      const records=[];
      for(let i=0;i<await images.count();i++) {
        const img=images.nth(i);
        await img.scrollIntoViewIfNeeded();
        await img.evaluate(el=>el.decode());
        records.push(await img.evaluate(el=>({
          src:el.getAttribute('src'),alt:(el.alt||'').trim(),
          w:el.width,h:el.height,nw:el.naturalWidth,nh:el.naturalHeight,
          dw:Number(el.getAttribute('width')),dh:Number(el.getAttribute('height')),
          caption:el.closest('figure')?.querySelector('figcaption')?.textContent.trim()||''
        })));
      }
      for(const x of records) {
        assert.ok(x.nw>0&&x.nh>0,`${route}: foto no decodificada ${x.src}`);
        assert.ok(x.alt.length>=20&&x.caption.length>=10,`${route}: foto sin descripción suficiente ${x.src}`);
        assert.ok(x.dw>0&&x.dh>0,`${route}: dimensiones declaradas ausentes`);
        assert.ok(Math.abs(x.dw/x.dh-x.nw/x.nh)<0.1,`${route}: proporción declarada incorrecta ${x.src}`);
      }
      assert.equal(new Set(records.map(x=>x.alt)).size,records.length,`${route}: fotografías con alt duplicado`);
      await page.close();
    }
  } finally {await context.close()}
} finally {await browser.close()}
console.log('OK: galerías documentales');