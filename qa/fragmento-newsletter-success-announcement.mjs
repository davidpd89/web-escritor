import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const BASE=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true});
try {
  for(const source of ['fragmento','explore']) {
    const ctx=await browser.newContext();
    await ctx.route('**/*',r=>r.request().url().startsWith('https://subscribe.davidpd89.workers.dev')?r.fulfill({status:201,contentType:'application/json',body:JSON.stringify({ok:true,state:'pending_confirmation'})}):r.request().url().startsWith(BASE)?r.continue():r.abort());
    const page=await ctx.newPage();
    await page.goto(BASE+'/fragmento/');
    if(source==='explore')await page.locator('[data-explore-open]').click();
    const form=page.locator('#newsletter-form-'+source);
    assert.equal(await form.locator('[role=status],[aria-live]').count(),1);
    await form.locator('input[type=email]').fill('lectora@example.com');
    await form.locator('[type=submit]').click();
    await page.waitForFunction(src=>/Revisa tu correo/i.test(document.querySelector('#newsletter-form-'+src)?.textContent||''),source);
    const announcements=await form.locator('[role=status],[aria-live]').allTextContents();
    assert.ok(announcements.some(text=>/Revisa tu correo/i.test(text)),`${source}: confirmación silenciosa para lectores de pantalla`);
    await ctx.close();
  }
} finally {await browser.close();}
console.log('fragmento-newsletter-success-announcement: OK');