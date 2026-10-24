import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true});
const cases=[{status:'open',direct:true},{status:'closed',country:'España'},{genre:'fantasía',status:'open'},{status:'unknown',direct:false},{country:'México',direct:true}];
try {
  const context=await browser.newContext({viewport:{width:1024,height:900}});
  const page=await context.newPage();
  try {
    await page.goto(`${BASE}/editoriales/`,{waitUntil:'load'});
    const data=await page.locator('[data-editorial-card]').evaluateAll(items=>items.map(el=>({name:el.dataset.name,status:el.dataset.status,country:el.dataset.country,genres:(el.dataset.genres||'').split('|'),direct:el.dataset.direct==='true'})));
    assert.ok(data.length>20);
    for(const c of cases) {
      await page.locator('[data-editoriales-reset]').click();
      if(c.status)await page.locator('[data-editoriales-status]').selectOption(c.status);
      if(c.country)await page.locator('[data-editoriales-country]').selectOption(c.country);
      if(c.genre)await page.locator('[data-editoriales-genre]').selectOption(c.genre);
      if(c.direct===true)await page.locator('[data-editoriales-direct]').check();
      const expected=data.filter(r=>(!c.status||r.status===c.status)&&(!c.country||r.country===c.country)&&(!c.genre||r.genres.includes(c.genre))&&(!c.direct||r.direct));
      const visible=await page.locator('[data-editorial-card]:visible').count();
      assert.equal(visible,expected.length,JSON.stringify(c));
      assert.equal((await page.locator('[data-editoriales-count]').innerText()).trim(),`${visible} ${visible===1?'editorial':'editoriales'}`);
      const hash=new URL(page.url()).hash;
      await page.locator('a[href="/metodologia-editorial/"]').first().click();
      await page.waitForURL('**/metodologia-editorial/');
      assert.equal(await page.locator('.spec-ledger dt').count(),5);
      await page.goBack({waitUntil:'domcontentloaded'});
      assert.equal(new URL(page.url()).hash,hash,'Filtro perdido en historial');
      assert.equal(await page.locator('[data-editorial-card]:visible').count(),expected.length);
    }
  } finally {await context.close();}
  console.log('PASS editorial methodology pairwise journey');
} finally {await browser.close();}