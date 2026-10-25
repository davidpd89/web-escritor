import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=process.env.QA_BASE_URL||'http://127.0.0.1:4173';
const browser=await chromium.launch();
const page=await browser.newPage();

async function state(){return page.evaluate(()=>({names:[...document.querySelectorAll('[data-editorial-card]')].filter(c=>!c.hidden).map(c=>c.dataset.name),count:document.querySelector('[data-editoriales-count]').textContent.trim()}));}

try {
  const response=await page.goto(BASE+'/editoriales/',{waitUntil:'domcontentloaded'});
  assert.ok(response?.ok());
  const initial=await state();
  await page.locator('[data-editoriales-search]').fill('fantasía');
  const pointer=await state();
  assert.ok(pointer.names.length>0);
  await page.locator('[data-editoriales-reset]').click();
  assert.deepEqual(await state(),initial);
  assert.equal(await page.evaluate(()=>document.activeElement?.id),'editoriales-q');

  await page.locator('[data-editoriales-search]').focus();
  await page.keyboard.type('fantasía');
  assert.deepEqual(await state(),pointer);
  await page.locator('[data-editoriales-reset]').focus();
  await page.keyboard.press('Enter');
  assert.deepEqual(await state(),initial);
  assert.equal(await page.evaluate(()=>document.activeElement?.id),'editoriales-q');

  await page.locator('[data-editoriales-direct]').check();
  const directPointer=await state();
  await page.locator('[data-editoriales-reset]').click();
  await page.locator('[data-editoriales-direct]').focus();
  await page.keyboard.press('Space');
  assert.deepEqual(await state(),directPointer);
  console.log('PASS editoriales input modality parity');
} finally {
  await browser.close();
}
