import assert from 'node:assert/strict';
import {chromium} from 'playwright';
const origin=process.env.QA_ORIGIN;
assert.ok(origin,'QA_ORIGIN obligatorio');
const browser=await chromium.launch({headless:true});
try {
  for(const width of [320,390]) {
    const page=await browser.newPage({viewport:{width,height:667},reducedMotion:'reduce'});
    try {
      await page.goto(new URL('/',origin).href,{waitUntil:'load'});
      await page.locator('.site-header').waitFor({state:'visible'});
      await page.evaluate(()=>document.fonts.ready);
      for(const position of [0,600,0]) {
        await page.evaluate(y=>window.scrollTo(0,y),position);
        await page.waitForFunction(y=>Math.abs(window.scrollY-Math.min(y,document.documentElement.scrollHeight-innerHeight))<5,position);
        const boxes=await page.evaluate(()=>{
          const selectors=['.site-header .explore-trigger','.site-header .header-buy'];
          return selectors.map(s=>{const el=document.querySelector(s);if(!el)return null;const r=el.getBoundingClientRect();return {selector:s,left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height,visible:getComputedStyle(el).visibility!=='hidden'&&getComputedStyle(el).display!=='none'};});
        });
        assert.ok(boxes.every(Boolean),`${width}px, scroll ${position}: faltan controles: ${JSON.stringify(boxes)}`);
        for(const r of boxes){assert.ok(r.visible&&r.left>=-1&&r.right<=width+1&&r.top>=-1&&r.bottom<=667+1,`${width}px, scroll ${position}: ${r.selector} fuera de pantalla: ${JSON.stringify(r)}`);}
        const [a,b]=boxes;
        assert.ok(a.right<=b.left+1||b.right<=a.left+1||a.bottom<=b.top+1||b.bottom<=a.top+1,`${width}px, scroll ${position}: Comprar y Explorar se solapan`);
      }
    }finally{await page.close();}
  }
}finally{await browser.close();}