import assert from 'node:assert/strict';
import { chromium } from 'playwright';

assert.ok(process.env.QA_ORIGIN,'Se necesita QA_ORIGIN');
const browser=await chromium.launch({headless:true});
try {
  for(const width of [320,390,768,1280]) {
    for(const scale of [1,2]) {
      const page=await browser.newPage({viewport:{width,height:800},reducedMotion:'reduce'});
      await page.addInitScript(()=>{try{sessionStorage.setItem('dp-intro-seen','true')}catch{}});
      await page.goto(new URL('/',process.env.QA_ORIGIN).href,{waitUntil:'load'});
      await page.evaluate(async scale=>{
        await document.fonts.ready;
        document.documentElement.style.fontSize=`${16*scale}px`;
      },scale);
      const result=await page.evaluate(()=>{
        const selectors='main .text-action,main .primary-action,main .ledger__action,footer .text-action';
        return [...document.querySelectorAll(selectors)].filter(el=>{
          const s=getComputedStyle(el);
          return s.display!=='none'&&s.visibility==='visible'&&el.getClientRects().length>0;
        }).map(el=>{
          const r=el.getBoundingClientRect();
          const s=getComputedStyle(el);
          return {label:el.textContent.trim().slice(0,80),left:r.left,right:r.right,width:r.width,height:r.height,fontSize:s.fontSize,valid:r.width>0&&r.height>0&&r.left>=-1&&r.right<=innerWidth+1};
        });
      });
      assert.ok(result.length>0,`Portada ${width}px escala ${scale}: sin acciones editoriales visibles`);
      for(const item of result) assert.ok(item.valid,`Portada ${width}px escala ${scale}: ${JSON.stringify(item)}`);
      await page.close();
    }
  }
}finally{await browser.close();}