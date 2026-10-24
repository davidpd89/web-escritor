import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const BASE=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true});
try {
  for(const blocked of ['getItem','setItem']) {
    const ctx=await browser.newContext({reducedMotion:'reduce'});
    await ctx.addInitScript(method=>{const original=Storage.prototype[method];Storage.prototype[method]=function(key,...args){if(key==='sticky-cta-dismissed')throw new DOMException('Storage blocked','SecurityError');return original.call(this,key,...args);};},blocked);
    const page=await ctx.newPage();
    const errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    await page.route('**/*',r=>r.request().url().startsWith(BASE)?r.continue():r.abort());
    await page.goto(BASE+'/fragmento/');
    await page.evaluate(()=>{scrollTo(0,(document.body.scrollHeight-innerHeight)*.7);dispatchEvent(new Event('scroll'));});
    await page.waitForTimeout(100);
    assert.equal(await page.locator('#sticky-cta').evaluate(e=>e.classList.contains('visible')),true,`${blocked}: barra inutilizada`);
    await page.locator('#sticky-cta-close').click();
    assert.equal(await page.locator('#sticky-cta').evaluate(e=>e.classList.contains('visible')),false);
    assert.deepEqual(errors.filter(e=>e.includes('Storage blocked')),[],`${blocked}: excepción sin capturar`);
    await ctx.close();
  }
} finally {await browser.close();}
console.log('fragmento-sticky-storage-exceptions: OK');