import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try {
  for(const width of [320,390,900,901,1440]) {
    const context=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce'});
    const page=await context.newPage();
    try {
      const response=await page.goto(`${ORIGIN}/eventos.html`,{waitUntil:'load'});
      assert.ok(response?.ok(),`/eventos.html ${width}px: carga fallida`);
      await page.evaluate(()=>document.fonts?.ready);
      const links=page.locator('#feria-libro-madrid-2026 .text-action');
      assert.ok(await links.count()>0,`/eventos.html ${width}px: falta la acción documental de Madrid`);
      for(let i=0;i<await links.count();i++) {
        const data=await links.nth(i).evaluate(el=>{
          const r=el.getBoundingClientRect(),parent=el.parentElement.getBoundingClientRect();
          const style=getComputedStyle(el);
          const range=document.createRange();range.selectNodeContents(el);
          const text=range.getBoundingClientRect();
          return {width:r.width,height:r.height,left:r.left,right:r.right,parentLeft:parent.left,parentRight:parent.right,textWidth:text.width,display:style.display,visibility:style.visibility};
        });
        assert.ok(data.height>0&&data.width>0,`/eventos.html ${width}px: acción ${i} sin caja visible`);
        assert.notEqual(data.visibility,'hidden',`/eventos.html ${width}px: acción ${i} oculta`);
        assert.ok(data.left>=data.parentLeft-1&&data.right<=data.parentRight+1,`/eventos.html ${width}px: acción ${i} sale de su columna: ${JSON.stringify(data)}`);
        if(width>=901&&data.textWidth>0) assert.ok(data.width<=data.textWidth+24,`/eventos.html ${width}px: acción ${i} estirada como divisor: caja ${data.width}px, texto ${data.textWidth}px`);
      }
    } finally {await context.close();}
  }
} finally {await browser.close();}
console.log('Acciones documentales: anchura natural OK');