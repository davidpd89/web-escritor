import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const BASE=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true});
try {
  const ctx=await browser.newContext({viewport:{width:390,height:900},reducedMotion:'reduce'});
  const page=await ctx.newPage();
  const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/*',r=>r.request().url().startsWith(BASE)?r.continue():r.abort());
  await page.goto(BASE+'/fragmento/');
  assert.equal(await page.locator('.reading-progress').count(),1);
  const samples=[];
  for(const ratio of [0,.2,.4,.6,.8,1,.8,.4,0]) {
    await page.evaluate(r=>{scrollTo(0,(document.documentElement.scrollHeight-innerHeight)*r);dispatchEvent(new Event('scroll'));},ratio);
    await page.waitForTimeout(80);
    const value=await page.locator('.reading-progress').evaluate(e=>parseFloat(e.style.width)||0);
    assert.ok(value>=0&&value<=100,`Progreso fuera de límites: ${value}`);
    assert.equal(await page.locator('.reading-progress').count(),1);
    samples.push(value);
  }
  for(let i=1;i<=5;i++)assert.ok(samples[i]>=samples[i-1],`No aumenta en ${i}`);
  for(let i=6;i<samples.length;i++)assert.ok(samples[i]<=samples[i-1],`No retrocede en ${i}`);
  assert.ok(samples[5]>90,'El final no registra lectura completa');
  assert.deepEqual(errors,[]);
  await ctx.close();
} finally {await browser.close();}
console.log('fragmento-reading-progress-stress: OK');