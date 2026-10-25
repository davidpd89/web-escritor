import assert from 'node:assert/strict';
import {chromium} from 'playwright';
const BASE=process.env.QA_BASE_URL||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try {
 for(const width of [320,390,768,1440]) {
  const page=await browser.newPage({viewport:{width,height:800}});
  try {
   await page.goto(BASE+'/libros/samuel-entre-mundos/',{waitUntil:'domcontentloaded'});
   await page.locator('main [data-buy-modal]').first().click();
   const dialog=page.locator('#buy-dialog');
   await dialog.waitFor({state:'visible'});
   for(const selector of ['.buy-option--primary','.buy-option:not(.buy-option--primary)']) {
    const link=dialog.locator(selector);
    await link.scrollIntoViewIfNeeded();
    const result=await link.evaluate(el=>{
      const r=el.getBoundingClientRect();
      const parse=c=>{const v=c.match(/[\d.]+/g)?.map(Number)||[];return v.slice(0,3).map(n=>n/255)};
      const lum=c=>{const a=parse(c).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);return .2126*a[0]+.7152*a[1]+.0722*a[2]};
      const samples=[...el.querySelectorAll('.buy-option-vendor,.buy-option-format,.buy-option-cta')];
      const bg=getComputedStyle(el).backgroundColor;
      return {box:{x:r.x,y:r.y,w:r.width,h:r.height},background:bg,contrast:samples.map(n=>{const fg=getComputedStyle(n).color;const a=lum(fg),b=lum(bg);return {text:n.textContent.trim(),ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05)}})};
    });
    const b=result.box;
    assert.ok(b.w>=24&&b.h>=24,`Samuel ${width} ${selector}: caja ${JSON.stringify(b)}`);
    assert.ok(b.x>=-1&&b.x+b.w<=width+1,`Samuel ${width} ${selector}: desbordamiento ${JSON.stringify(b)}`);
    assert.ok(b.y>=-1&&b.y+b.h<=801,`Samuel ${width} ${selector}: fuera de altura ${JSON.stringify(b)}`);
    assert.ok(result.contrast.length>0,`Samuel ${width} ${selector}: sin textos`);
    for(const sample of result.contrast) assert.ok(sample.ratio>=4.5,`Samuel ${width} ${selector} ${sample.text}: contraste ${sample.ratio.toFixed(2)} fondo ${result.background}`);
   }
  } finally {await page.close();}
 }
} finally {await browser.close();}
