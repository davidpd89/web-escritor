import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const base=(process.env.SITE_BASE_URL||'http://127.0.0.1:8000').replace(/\/$/,'');
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try{
  for(const width of [320,768,1024,1440]){
    const page=await browser.newPage({viewport:{width,height:900}});
    const route='/recomendaciones/';
    const response=await page.goto(base+route,{waitUntil:'domcontentloaded'});
    assert.equal(response.status(),200,`${route} ${width}px: HTTP inesperado`);
    await page.locator('.catalogue-card').first().waitFor({state:'visible'});
    await page.evaluate(()=>document.fonts.ready);
    const data=await page.evaluate(()=>{
      const grid=document.querySelector('.catalogue-grid');
      const container=grid.getBoundingClientRect();
      const cards=[...grid.querySelectorAll('.catalogue-card')].filter(e=>e.getClientRects().length).slice(0,12).map(e=>{const r=e.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width};});
      return {container:{left:container.left,right:container.right},cards};
    });
    assert.ok(data.cards.length>=2,`${route} ${width}px: menos de dos tarjetas visibles`);
    for(const [i,c] of data.cards.entries()){
      assert.ok(c.left>=data.container.left-2&&c.right<=data.container.right+2,`${route} ${width}px: tarjeta ${i+1} desborda su grid`);
      assert.ok(c.width>=Math.min(130,width*.4),`${route} ${width}px: tarjeta ${i+1} demasiado estrecha (${c.width}px)`);
      for(let j=0;j<i;j++){
        const b=data.cards[j];
        const overlapX=Math.min(c.right,b.right)-Math.max(c.left,b.left);
        const overlapY=Math.min(c.bottom,b.bottom)-Math.max(c.top,b.top);
        assert.ok(overlapX<=1||overlapY<=1,`${route} ${width}px: tarjetas ${j+1} y ${i+1} se solapan (${overlapX.toFixed(1)} x ${overlapY.toFixed(1)}px)`);
      }
    }
    await page.close();
  }
}finally{await browser.close();}
console.log('PASS: distribución responsive del catálogo');
