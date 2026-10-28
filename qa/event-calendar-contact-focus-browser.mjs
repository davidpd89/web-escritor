import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try {
  for(const width of [320,390,768,1440]) {
    const context=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce'});
    const page=await context.newPage();
    try {
      const response=await page.goto(`${ORIGIN}/eventos.html`,{waitUntil:'load'});
      assert.ok(response?.ok(),`/eventos.html ${width}px: carga fallida`);
      await page.evaluate(()=>document.fonts?.ready);
      const links=page.locator('#organizar .contact-card a[href]:visible');
      const count=await links.count();
      assert.ok(count>0,`/eventos.html ${width}px: directorio sin enlaces visibles`);
      for(let i=0;i<count;i++) {
        const link=links.nth(i);
        await link.scrollIntoViewIfNeeded();
        await link.focus();
        const result=await link.evaluate(el=>{
          const s=getComputedStyle(el),r=el.getBoundingClientRect();
          return {focused:document.activeElement===el,outlineStyle:s.outlineStyle,outlineWidth:parseFloat(s.outlineWidth),boxShadow:s.boxShadow,borderStyle:s.borderStyle,borderWidth:parseFloat(s.borderWidth),width:r.width,height:r.height,left:r.left,right:r.right};
        });
        assert.ok(result.focused,`/eventos.html ${width}px: enlace de contacto ${i} no recibe foco`);
        assert.ok(result.width>0&&result.height>0,`/eventos.html ${width}px: enlace ${i} sin caja`);
        assert.ok(result.left>=-1&&result.right<=width+1,`/eventos.html ${width}px: enlace ${i} fuera del viewport ${JSON.stringify(result)}`);
        const indicator=(result.outlineStyle!=='none'&&result.outlineWidth>=1)||result.boxShadow!=='none'||(result.borderStyle!=='none'&&result.borderWidth>=1);
        assert.ok(indicator,`/eventos.html ${width}px: enlace ${i} sin indicador de foco computado`);
      }
    } finally {await context.close();}
  }
} finally {await browser.close();}
console.log('Contactos de agenda: foco visible OK');