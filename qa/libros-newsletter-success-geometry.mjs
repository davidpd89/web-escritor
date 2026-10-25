import assert from 'node:assert/strict';
import {chromium} from 'playwright';
const BASE=process.env.QA_BASE_URL||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try {
 for(const route of ['/libros/','/libros/samuel-entre-mundos/']) {
  for(const width of [320,390,768]) {
   const context=await browser.newContext({viewport:{width,height:700}});
   try {
    await context.route('https://subscribe.davidpd89.workers.dev/**',route=>route.fulfill({status:200,contentType:'application/json',headers:{'access-control-allow-origin':'*'},body:JSON.stringify({ok:true,state:'pending_confirmation'})}));
    const page=await context.newPage();
    await page.goto(BASE+route,{waitUntil:'domcontentloaded'});
    await page.locator('[data-explore-open]').click();
    const form=page.locator('#newsletter-form-explore');
    await form.locator('input[type=email]').fill('lector@example.com');
    await form.locator('button[type=submit]').click();
    const success=form.locator('.quiz-subscribe-ok');
    await success.waitFor({state:'visible'});
    await success.scrollIntoViewIfNeeded();
    const m=await success.evaluate(el=>{const r=el.getBoundingClientRect();const s=getComputedStyle(el);return {x:r.x,y:r.y,w:r.width,h:r.height,scroll:el.scrollWidth,client:el.clientWidth,font:parseFloat(s.fontSize),text:el.textContent.trim()}});
    assert.match(m.text,/Solicitud recibida/,`${route} ${width}: confirmación incorrecta`);
    assert.ok(m.w>0&&m.h>0&&m.font>=12,`${route} ${width}: confirmación ilegible ${JSON.stringify(m)}`);
    assert.ok(m.x>=-1&&m.x+m.w<=width+1,`${route} ${width}: confirmación fuera de viewport ${JSON.stringify(m)}`);
    assert.ok(m.scroll<=m.client+1,`${route} ${width}: confirmación recortada ${JSON.stringify(m)}`);
   } finally {await context.close();}
  }
 }
} finally {await browser.close();}
