import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const BASE=process.env.QA_BASE_URL||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try {
 for(const route of ['/libros/','/libros/samuel-entre-mundos/']) {
  for(const width of [320,390,768]) {
   const page=await browser.newPage({viewport:{width,height:700}});
   try {
    await page.goto(BASE+route,{waitUntil:'domcontentloaded'});
    await page.locator('[data-explore-open]').click();
    const form=page.locator('#newsletter-form-explore');
    await form.locator('input[type=email]').fill('correo-invalido');
    await form.locator('button[type=submit]').click();
    const status=form.locator('[role=status]');
    await assert.doesNotReject(()=>status.getByText('Introduce un email válido.').waitFor({state:'visible'}),`${route} ${width}: validación no visible`);
    await status.scrollIntoViewIfNeeded();
    const result=await status.evaluate(el=>{
      const r=el.getBoundingClientRect();const s=getComputedStyle(el);
      return {x:r.x,y:r.y,w:r.width,h:r.height,scroll:el.scrollWidth,client:el.clientWidth,display:s.display,visibility:s.visibility,font:parseFloat(s.fontSize)};
    });
    assert.ok(result.w>0&&result.h>0&&result.font>=12,`${route} ${width}: mensaje ilegible ${JSON.stringify(result)}`);
    assert.ok(result.x>=-1&&result.x+result.w<=width+1,`${route} ${width}: mensaje fuera de pantalla ${JSON.stringify(result)}`);
    assert.ok(result.scroll<=result.client+1,`${route} ${width}: texto recortado ${JSON.stringify(result)}`);
    assert.equal(await form.locator('input[type=email]').evaluate(el=>document.activeElement===el),true,`${route} ${width}: foco de corrección`);
    await form.locator('input[type=email]').fill('lector@example.com');
    assert.equal(await form.locator('button[type=submit]').isEnabled(),true,`${route} ${width}: reintento bloqueado`);
   } finally {await page.close();}
  }
 }
} finally {await browser.close();}
