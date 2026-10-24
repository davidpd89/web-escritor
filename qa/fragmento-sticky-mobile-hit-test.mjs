import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const BASE=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true});
try {
  for(const [width,height] of [[320,568],[360,640],[390,667],[568,320]]) {
    const ctx=await browser.newContext({viewport:{width,height},reducedMotion:'reduce',hasTouch:true});
    const page=await ctx.newPage();
    await page.route('**/*',r=>r.request().url().startsWith(BASE)?r.continue():r.abort());
    await page.goto(BASE+'/fragmento/');
    await page.evaluate(()=>{scrollTo(0,(document.body.scrollHeight-innerHeight)*.7);dispatchEvent(new Event('scroll'));});
    await page.waitForFunction(()=>document.querySelector('#sticky-cta').classList.contains('visible'));
    for(const selector of ['#sticky-cta .primary-action','#sticky-cta .text-action','#sticky-cta-close']) {
      const rect=await page.locator(selector).boundingBox();
      assert.ok(rect&&rect.width>0&&rect.height>0,`${width}x${height} ${selector}: sin superficie`);
      const x=rect.x+rect.width/2,y=rect.y+rect.height/2;
      assert.ok(x>=0&&x<width&&y>=0&&y<height,`${selector}: fuera de pantalla`);
      const reachable=await page.evaluate(({selector,x,y})=>{const el=document.querySelector(selector);const hit=document.elementFromPoint(x,y);return hit===el||el.contains(hit);},{selector,x,y});
      assert.ok(reachable,`${width}x${height} ${selector}: otro elemento intercepta el toque`);
    }
    await page.locator('#sticky-cta-close').tap();
    assert.equal(await page.locator('#sticky-cta').evaluate(e=>e.classList.contains('visible')),false);
    await ctx.close();
  }
} finally {await browser.close();}
console.log('fragmento-sticky-mobile-hit-test: OK');