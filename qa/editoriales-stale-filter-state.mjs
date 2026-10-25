import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=process.env.QA_BASE_URL||'http://127.0.0.1:4173';
const browser=await chromium.launch();
const page=await browser.newPage();

async function check(query){
  await page.waitForFunction(q=>document.querySelector('[data-editoriales-search]').value===q,query);
  const cards=await page.locator('[data-editorial-card]:visible').count();
  const count=await page.locator('[data-editoriales-count]').innerText();
  assert.equal(Number(count.match(/^\d+/)?.[0]),cards);
}

try {
  const response=await page.goto(BASE+'/editoriales/',{waitUntil:'domcontentloaded'});
  assert.ok(response?.ok());
  for(const [first,second] of [['fantasía','terror'],['poesía','narrativa'],['ensayo','romance']]){
    await page.locator('[data-editoriales-search]').fill(first);
    await check(first);
    await page.evaluate(q=>{location.hash='#q='+encodeURIComponent(q)},second);
    await check(second);
    await page.locator('[data-editoriales-search]').fill(first);
    await check(first);
    assert.equal(new URLSearchParams(new URL(page.url()).hash.slice(1)).get('q'),first);
  }
  console.log('PASS editoriales stale filter state');
} finally {
  await browser.close();
}
