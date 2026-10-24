import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const BASE=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true});
try {
  for(const width of [320,390,768])for(const count of [60,160,400]) {
    const ctx=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce'});
    const page=await ctx.newPage();
    await page.route('**/*',r=>r.request().url().startsWith(BASE)?r.continue():r.abort());
    await page.goto(BASE+'/fragmento/');
    await page.evaluate(n=>{document.querySelector('.fragment-cta-box h2').textContent='La continuación de la historia '.repeat(n/10);document.querySelector('.fragment-cta-actions .primary-action').textContent='Continuar leyendo sin abandonar la página '.repeat(n/15);},count);
    await page.waitForTimeout(40);
    const overflow=await page.evaluate(()=>document.documentElement.scrollWidth-document.documentElement.clientWidth);
    assert.ok(overflow<=1,`${width}px / ${count}: overflow ${overflow}px`);
    for(const selector of ['.fragment-cta-actions .primary-action','.fragment-cta-actions .text-action']) {
      const r=await page.locator(selector).first().boundingBox();
      assert.ok(r&&r.width>0&&r.x>=-1&&r.x+r.width<=width+1,`${selector}: geometría rota`);
    }
    await ctx.close();
  }
} finally {await browser.close();}
console.log('fragmento-content-length-mutations: OK');