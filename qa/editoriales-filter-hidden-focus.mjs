import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE=process.env.QA_BASE_URL||process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try {
 const page=await browser.newPage();
 const response=await page.goto(`${BASE}/editoriales/`,{waitUntil:'domcontentloaded'});
 assert.ok(response?.ok(),'/editoriales/: error HTTP');
 const status=page.locator('[data-editoriales-status]');
 for(const value of ['open','closed']) {
   await status.selectOption(value);
   await page.waitForFunction(v=>[...document.querySelectorAll('[data-editorial-card]')].every(el=>el.hidden === (el.dataset.status!==v)),value);
   const result=await page.evaluate(()=>{
     const cards=[...document.querySelectorAll('[data-editorial-card]')];
     const hidden=cards.filter(c=>c.hidden);
     const visible=cards.filter(c=>!c.hidden);
     return {hidden:hidden.length,visible:visible.length,violations:hidden.flatMap(c=>[...c.querySelectorAll('a,button,input,select,[tabindex]')].filter(el=>el.tabIndex>=0&&el.getClientRects().length).map(el=>el.outerHTML.slice(0,120)))};
   });
   assert.ok(result.hidden>0&&result.visible>0,`/editoriales/: partición ${value} sin fichas visibles y ocultas`);
   assert.deepEqual(result.violations,[],`/editoriales/: controles de fichas ocultas expuestos con estado ${value}`);
   const first=page.locator('[data-editorial-card]:visible a[href]').first();
   await first.focus();
   assert.equal(await first.evaluate(el=>document.activeElement===el),true,`/editoriales/: enlace visible inaccesible con estado ${value}`);
 }
} finally {await browser.close();}
