import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const BASE=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true});
const cases=[['empty','',false],['without-at','usuario.example.com',false],['local-65','a'.repeat(65)+'@example.com',false],['with-space','a b@example.com',false],['local-64','a'.repeat(64)+'@example.com',true],['normal','lectora@example.com',true]];
try {
  for(const source of ['fragmento','explore'])for(const [label,value,valid] of cases) {
    const ctx=await browser.newContext();
    const requests=[];
    await ctx.route('**/*',async r=>{const url=r.request().url();if(url.startsWith('https://subscribe.davidpd89.workers.dev')){requests.push(r.request().postDataJSON());return r.fulfill({status:201,contentType:'application/json',body:JSON.stringify({ok:true,state:'pending_confirmation'})});}return url.startsWith(BASE)?r.continue():r.abort();});
    const page=await ctx.newPage();
    await page.goto(BASE+'/fragmento/');
    if(source==='explore')await page.locator('[data-explore-open]').click();
    const form=page.locator('#newsletter-form-'+source);
    await form.locator('input[type=email]').fill(value);
    await form.evaluate(e=>e.requestSubmit());
    await page.waitForTimeout(150);
    assert.equal(requests.length,valid?1:0,`${source}/${label}: solicitudes incorrectas`);
    if(valid){assert.equal(requests[0].source,source);assert.equal(requests[0].email,value);}
    await ctx.close();
  }
} finally {await browser.close();}
console.log('fragmento-newsletter-email-boundaries: OK');