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
      const opener=page.locator('[data-explore-open]:visible').first();
      const dialog=page.locator('[data-explore-dialog]');
      for(let cycle=0;cycle<6;cycle++){
        await opener.click();
        await dialog.waitFor({state:'visible'});
        assert.equal(await opener.getAttribute('aria-expanded'),'true',`${width}px, ciclo ${cycle}: disparador no refleja apertura`);
        if(cycle%2===0)await page.keyboard.press('Escape');
        else await dialog.locator('[data-explore-close]').click();
        await page.waitForFunction(()=>!document.querySelector('[data-explore-dialog]').open);
        assert.equal(await opener.getAttribute('aria-expanded'),'false',`${width}px, ciclo ${cycle}: aria-expanded residual`);
        assert.equal(await page.locator('html').evaluate(el=>el.classList.contains('explore-open')),false,`${width}px, ciclo ${cycle}: bloqueo residual del documento`);
        assert.ok(await opener.isEnabled(),`${width}px, ciclo ${cycle}: no puede reabrirse el menú`);
      }
    }finally{await page.close();}
  }
}finally{await browser.close();}