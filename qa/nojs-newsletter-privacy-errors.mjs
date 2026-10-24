import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const O=(process.env.QA_ORIGIN||'http://127.0.0.1:4173').replace(/\/$/,'');
const email='qa-nojs@example.invalid';
const browser=await chromium.launch({headless:true});
try{
  const plain=await browser.newContext({javaScriptEnabled:false});
  await plain.route('**/*',r=>r.request().url().startsWith(O+'/')?r.continue():r.abort());
  const nojs=await plain.newPage();
  await nojs.goto(O+'/cuaderno/',{waitUntil:'load'});
  const form=nojs.locator('#newsletter-form-cuaderno');
  assert.equal(await form.count(),1,'Formulario ausente');
  if(await form.isVisible()){
    await form.locator('input[type=email]').fill(email);
    await Promise.allSettled([nojs.waitForNavigation({timeout:2500}),form.locator('[type=submit]').click()]);
    assert.ok(!decodeURIComponent(nojs.url()).includes(email),'Email expuesto en URL sin JavaScript');
  }
  await plain.close();
  for(const code of [429,503]){
    const context=await browser.newContext();
    await context.route('**/*',r=>{const u=r.request().url();if(u.startsWith('https://subscribe.davidpd89.workers.dev'))return r.fulfill({status:code,contentType:'application/json',body:'{}',headers:{'access-control-allow-origin':O}});return u.startsWith(O+'/')?r.continue():r.abort();});
    const page=await context.newPage();
    await page.goto(O+'/cuaderno/',{waitUntil:'load'});
    const f=page.locator('#newsletter-form-cuaderno');
    await f.locator('input[type=email]').fill(email);
    await f.locator('[type=submit]').click();
    await f.locator('[role=status]').filter({hasText:code===429?/demasiados intentos/i:/error al suscribirse/i}).waitFor({state:'visible',timeout:5000});
    assert.equal(await f.locator('[type=submit]').isEnabled(),true,code+': submit bloqueado');
    assert.equal(await f.locator('input[type=email]').inputValue(),email,code+': email perdido');
    assert.ok((await f.locator('a[href="/privacidad.html"]').count())>0,code+': política inaccesible');
    await context.close();
  }
}finally{await browser.close();}
console.log('PASS nojs newsletter privacy and error recovery');