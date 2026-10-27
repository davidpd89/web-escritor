import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN=(process.env.QA_ORIGIN||process.env.SITE_BASE_URL||'http://127.0.0.1:4173').replace(/\/$/,'');
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try {
  for(const width of [390,1280]) {
    const context=await browser.newContext({javaScriptEnabled:false,viewport:{width,height:900}});
    const page=await context.newPage();
    const response=await page.goto(ORIGIN+'/editoriales/',{waitUntil:'load'});
    assert.equal(response?.status(),200,`/editoriales/@${width}: HTTP`);
    const controls=page.locator('[data-editoriales-search],[data-editoriales-genre],[data-editoriales-status],[data-editoriales-country],[data-editoriales-sort],[data-editoriales-direct]');
    assert(await controls.count()>0,`/editoriales/@${width}: faltan controles reales`);
    for(let i=0;i<await controls.count();i++) {
      const control=controls.nth(i);
      if(!await control.isVisible()||!await control.isEnabled())continue;
      const before=await page.locator('[data-editorial-card]:visible').count();
      const tag=await control.evaluate(e=>e.tagName.toLowerCase());
      if(tag==='select') {
        const values=await control.locator('option:not([disabled])').evaluateAll(ns=>ns.map(n=>n.value));
        const current=await control.inputValue();
        const alternative=values.find(v=>v!==current);
        if(alternative===undefined)continue;
        await control.selectOption(alternative);
      } else if(await control.getAttribute('type')==='checkbox') {
        await control.check();
      } else {
        await control.fill('Minotauro');
        await control.press('Enter');
      }
      const after=await page.locator('[data-editorial-card]:visible').count();
      const navigated=new URL(page.url()).pathname!=='/editoriales/';
      const disabled=!(await control.isEnabled().catch(()=>false));
      assert(navigated||after!==before||disabled,`/editoriales/@${width}: control ${i} (${tag}) parece operativo sin JS pero no altera resultados ni navega; antes=${before}, después=${after}`);
      if(navigated)break;
    }
    await context.close();
  }
  console.log('PASS editoriales no-JS filter affordance');
} finally {await browser.close();}
