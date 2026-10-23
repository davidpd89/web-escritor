import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const O=(process.env.QA_ORIGIN||'http://127.0.0.1:4173').replace(/\/$/,'');
const CASES=[{url:'/editoriales/',search:'[data-editoriales-search]',card:'[data-editorial-card]',empty:'[data-editoriales-empty]',reset:'[data-editoriales-reset]'},{url:'/convocatorias-escritores/',search:'[data-radar-search]',card:'[data-radar-item]',empty:'[data-radar-filter-empty]',reset:'[data-radar-empty-clear]'}];
const browser=await chromium.launch({headless:true});
try{
  const context=await browser.newContext();
  await context.route('**/*',r=>r.request().url().startsWith(O+'/')?r.continue():r.abort());
  const page=await context.newPage();
  for(const test of CASES){
    await page.goto(O+test.url,{waitUntil:'load'});
    const baseline=await page.locator(test.card+':visible').count();
    assert.ok(baseline>0,test.url+': sin resultados iniciales');
    await page.locator(test.search).fill('qa_impossible_zzzz_987654321');
    await page.locator(test.empty).waitFor({state:'visible'});
    assert.equal(await page.locator(test.card+':visible').count(),0,test.url+': quedan resultados visibles');
    assert.ok((await page.locator(test.empty).innerText()).trim().length>15,test.url+': estado vacío sin explicación');
    await page.locator(test.reset).click();
    await page.waitForFunction(selector=>[...document.querySelectorAll(selector)].some(e=>e.getClientRects().length&&!e.hidden),test.card);
    assert.ok(await page.locator(test.card+':visible').count()>0,test.url+': reset no recupera resultados');
    assert.equal(await page.locator(test.search).inputValue(),'',test.url+': búsqueda residual');
  }
  await context.close();
}finally{await browser.close();}
console.log('PASS dynamic empty reset matrix');