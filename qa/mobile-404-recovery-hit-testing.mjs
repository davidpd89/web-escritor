import assert from 'node:assert/strict';
import {chromium} from 'playwright';
const origin=process.env.QA_ORIGIN;
assert.ok(origin,'QA_ORIGIN obligatorio');
const browser=await chromium.launch({headless:true});
try{
  for(const width of [320,390]){
    const page=await browser.newPage({viewport:{width,height:667},reducedMotion:'reduce'});
    try{
      await page.goto(new URL('/404.html',origin).href,{waitUntil:'load'});
      await page.evaluate(()=>document.fonts.ready);
      const links=page.locator('main a[href^="/"]:visible');
      const count=await links.count();
      assert.ok(count>0,`${width}px: la página 404 no tiene enlaces internos de recuperación`);
      for(let i=0;i<count;i++){
        const link=links.nth(i);
        await link.scrollIntoViewIfNeeded();
        const result=await link.evaluate(el=>{
          const r=el.getBoundingClientRect();
          const x=r.left+r.width/2,y=r.top+r.height/2;
          const hit=document.elementFromPoint(x,y);
          return {href:el.getAttribute('href'),left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height,hit:!!hit&&(hit===el||el.contains(hit))};
        });
        assert.ok(result.left>=-1&&result.right<=width+1,`${width}px: ${result.href} recortado: ${JSON.stringify(result)}`);
        assert.ok(result.width>0&&result.height>0&&result.hit,`${width}px: ${result.href} no recibe contacto en su centro: ${JSON.stringify(result)}`);
      }
    }finally{await page.close();}
  }
}finally{await browser.close();}