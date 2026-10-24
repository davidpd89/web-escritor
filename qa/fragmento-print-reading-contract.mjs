import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const BASE=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true});
try {
  const ctx=await browser.newContext({viewport:{width:1200,height:900}});
  const page=await ctx.newPage();
  await page.route('**/*',r=>r.request().url().startsWith(BASE)?r.continue():r.abort());
  await page.goto(BASE+'/fragmento/');
  const original=await page.locator('.fragment-reading').innerText();
  assert.ok(original.length>5000);
  await page.emulateMedia({media:'print'});
  for(const selector of ['.fragment-reading','.fragment-reading h2','.fragment-reading p','.fragment-divider']) {
    assert.ok(await page.locator(selector).first().isVisible(),`${selector}: contenido ausente al imprimir`);
  }
  for(const selector of ['#sticky-cta','.editorial-newsletter']) {
    assert.equal(await page.locator(selector).isVisible(),false,`${selector}: aparece en impresión`);
  }
  assert.equal(await page.locator('.fragment-reading').innerText(),original,'El modo impresión altera el capítulo');
  const style=await page.locator('.fragment-reading p').first().evaluate(e=>getComputedStyle(e));
  assert.notEqual(style.visibility,'hidden');
  await ctx.close();
} finally {await browser.close();}
console.log('fragmento-print-reading-contract: OK');