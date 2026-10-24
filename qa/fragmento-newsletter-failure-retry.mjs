import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const BASE=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true});
try {
  const ctx=await browser.newContext();
  let calls=0;
  await ctx.route('**/*',async r=>{const url=r.request().url();if(url.startsWith('https://subscribe.davidpd89.workers.dev')){calls++;if(calls===1)return r.fulfill({status:500,contentType:'application/json',body:'{}'});return r.fulfill({status:201,contentType:'application/json',body:JSON.stringify({ok:true,state:'pending_confirmation'})});}return url.startsWith(BASE)?r.continue():r.abort();});
  const page=await ctx.newPage();
  await page.goto(BASE+'/fragmento/');
  const form=page.locator('#newsletter-form-fragmento');
  const button=form.locator('[type=submit]');
  const original=(await button.innerText()).trim();
  await form.locator('input[type=email]').fill('lectora@example.com');
  await button.click();
  await page.waitForFunction(()=>/Error al suscribirse/i.test(document.querySelector('#nl-status-fragmento')?.textContent||''));
  assert.equal(calls,1);
  assert.equal(await button.isEnabled(),true);
  assert.equal((await button.innerText()).trim(),original,'La recuperación modifica la etiqueta editorial');
  assert.equal(await form.locator('input[type=email]').inputValue(),'lectora@example.com');
  await button.click();
  await page.waitForFunction(()=>/Revisa tu correo/i.test(document.querySelector('#newsletter-form-fragmento')?.textContent||''));
  assert.equal(calls,2);
  await ctx.close();
} finally {await browser.close();}
console.log('fragmento-newsletter-failure-retry: OK');