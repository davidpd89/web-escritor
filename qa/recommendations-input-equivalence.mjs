import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const BASE=process.env.RECOMMENDATIONS_BASE_URL||'http://127.0.0.1:4173';
const browser=await chromium.launch();
try{
 const context=await browser.newContext();
 await context.route(/^https?:\/\//,r=>new URL(r.request().url()).origin===new URL(BASE).origin?r.continue():r.abort());
 const results=[];
 for(const modality of ['pointer','keyboard']){
  const page=await context.newPage();
  await page.goto(BASE+'/recomendaciones/');
  const target=page.locator('input[data-facet]:enabled').first();
  assert.equal(await target.count(),1);
  await target.evaluate(el=>el.closest('details').open=true);
  if(modality==='pointer')await target.check();
  else{await target.focus();await page.keyboard.press('Space');}
  assert.ok(await target.isChecked());
  results.push(await page.evaluate(()=>({ids:[...document.querySelectorAll('[data-catalogue-book]')].filter(x=>!x.hidden).map(x=>x.dataset.bookId),hash:location.hash})));
  await page.close();
 }
 assert.deepEqual(results[0],results[1]);
 console.log('PASS input modality equivalence');
}finally{await browser.close();}