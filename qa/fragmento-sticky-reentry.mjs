import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const BASE=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true});
try {
  for(const width of [390,1280]) {
    const ctx=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce'});
    const page=await ctx.newPage();
    await page.route('**/*',r=>r.request().url().startsWith(BASE)?r.continue():r.abort());
    await page.goto(BASE+'/fragmento/');
    const cases=[[0,false],[.64,false],[.70,true],[.95,false],[.70,true],[.20,false],[.75,true],[1,false]];
    for(const [ratio,expected] of cases) {
      await page.evaluate(v=>{scrollTo(0,(document.body.scrollHeight-innerHeight)*v);dispatchEvent(new Event('scroll'));},ratio);
      await page.waitForTimeout(90);
      const visible=await page.locator('#sticky-cta').evaluate(e=>e.classList.contains('visible'));
      assert.equal(visible,expected,`${width}px, scroll ${ratio}: transición incorrecta`);
    }
    await ctx.close();
  }
} finally {await browser.close();}
console.log('fragmento-sticky-reentry: OK');