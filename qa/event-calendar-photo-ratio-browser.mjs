import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try {
  for(const width of [320,390,768,900,901,1440]) {
    const context=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce'});
    const page=await context.newPage();
    try {
      const response=await page.goto(`${ORIGIN}/eventos.html`,{waitUntil:'load'});
      assert.ok(response?.ok(),`/eventos.html ${width}px: carga fallida`);
      const photo=page.locator('#feria-libro-madrid-2026 figure img');
      assert.equal(await photo.count(),1,`/eventos.html ${width}px: fotografía documental ausente o duplicada`);
      await photo.scrollIntoViewIfNeeded();
      await photo.evaluate(async img=>{if(!img.complete) await new Promise((resolve,reject)=>{img.addEventListener('load',resolve,{once:true});img.addEventListener('error',reject,{once:true});});});
      const data=await photo.evaluate(img=>{
        const r=img.getBoundingClientRect(),figure=img.closest('figure').getBoundingClientRect();
        const style=getComputedStyle(img);
        return {naturalWidth:img.naturalWidth,naturalHeight:img.naturalHeight,width:r.width,height:r.height,left:r.left,right:r.right,figureWidth:figure.width,objectFit:style.objectFit};
      });
      assert.ok(data.naturalWidth>0&&data.naturalHeight>0,`/eventos.html ${width}px: fotografía sin dimensiones naturales`);
      assert.ok(data.width>0&&data.height>0,`/eventos.html ${width}px: fotografía colapsada`);
      assert.ok(data.left>=-1&&data.right<=width+1,`/eventos.html ${width}px: fotografía fuera del viewport ${JSON.stringify(data)}`);
      assert.ok(data.width<=data.figureWidth+1,`/eventos.html ${width}px: imagen desborda figure`);
      const natural=data.naturalWidth/data.naturalHeight;
      const rendered=data.width/data.height;
      assert.ok(Math.abs(natural-rendered)<.02,`/eventos.html ${width}px: imagen deformada, proporción natural ${natural}, renderizada ${rendered}`);
    } finally {await context.close();}
  }
} finally {await browser.close();}
console.log('Fotografía documental: proporciones OK');