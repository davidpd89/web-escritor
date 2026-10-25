import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const browser=await chromium.launch({headless:true});
const page=await browser.newPage();
try {
  await page.goto((process.env.QA_ORIGIN||'http://127.0.0.1:4173')+'/editoriales/');
  const search=page.locator('[data-editoriales-search]');
  const count=page.locator('[data-editoriales-count]');
  const empty=page.locator('[data-editoriales-empty]');
  assert.equal(await count.getAttribute('role'),'status');
  assert.equal(await count.getAttribute('aria-live'),'polite');
  for(const query of ['Minotauro','zzzxqeditorialinexistente','Nocturna','']) {
    await search.fill(query);
    const n=await page.locator('[data-editorial-card]:visible').count();
    const text=await count.innerText();
    assert.match(text,new RegExp('^'+n+' editoriales?$'),query);
    assert.equal(await empty.isVisible(),n===0,query);
  }
  console.log('PASS accessible result lifecycle');
} finally {await browser.close();}
