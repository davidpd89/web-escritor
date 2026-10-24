import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const BASE=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true});
try {
  const destinations=[];
  for(const mode of ['mouse','keyboard']) {
    const ctx=await browser.newContext({reducedMotion:'reduce'});
    const page=await ctx.newPage();
    await page.route('**/*',r=>r.request().url().startsWith(BASE)?r.continue():r.abort());
    await page.goto(BASE+'/fragmento/');
    await page.evaluate(()=>{scrollTo(0,(document.body.scrollHeight-innerHeight)*.7);dispatchEvent(new Event('scroll'));});
    await page.waitForFunction(()=>document.querySelector('#sticky-cta').classList.contains('visible'));
    const link=page.locator('#sticky-cta a[href^="/libros/samuel-entre-mundos/#comprar"]');
    assert.equal(await link.count(),1);
    if(mode==='keyboard'){await link.focus();await link.press('Enter');}else{await link.click();}
    await page.waitForURL('**/libros/samuel-entre-mundos/#comprar');
    assert.equal(await page.locator('#comprar').count(),1);
    assert.ok(await page.locator('#comprar').isVisible());
    assert.ok(await page.locator('#comprar a').count()>0);
    destinations.push(new URL(page.url()).pathname+new URL(page.url()).hash);
    await ctx.close();
  }
  assert.equal(destinations[0],destinations[1]);
} finally {await browser.close();}
console.log('fragmento-buy-journey-modality: OK');