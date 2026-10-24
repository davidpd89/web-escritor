import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const BASE=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true});
try {
  for(const width of [320,390,1280]) {
    const ctx=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce'});
    const page=await ctx.newPage();
    await page.route('**/*',r=>r.request().url().startsWith(BASE)?r.continue():r.abort());
    await page.goto(BASE+'/fragmento/');
    async function focusable(){return page.evaluate(()=>{const a=document.querySelector('#sticky-cta a');a.focus({preventScroll:true});return document.activeElement===a;});}
    assert.equal(await page.locator('#sticky-cta').evaluate(e=>e.classList.contains('visible')),false);
    assert.equal(await focusable(),false,`${width}: enlace del CTA oculto recibe foco`);
    await page.evaluate(()=>{scrollTo(0,(document.body.scrollHeight-innerHeight)*.7);dispatchEvent(new Event('scroll'));});
    await page.waitForFunction(()=>document.querySelector('#sticky-cta').classList.contains('visible'));
    assert.equal(await focusable(),true,`${width}: enlace visible no recibe foco`);
    await page.evaluate(()=>{scrollTo(0,(document.body.scrollHeight-innerHeight)*.96);dispatchEvent(new Event('scroll'));});
    await page.waitForTimeout(100);
    assert.equal(await focusable(),false,`${width}: enlace vuelve a recibir foco tras ocultarse`);
    await ctx.close();
  }
} finally {await browser.close();}
console.log('fragmento-hidden-sticky-focus: OK');