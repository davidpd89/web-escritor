import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const browser=await chromium.launch({headless:true});
const context=await browser.newContext({javaScriptEnabled:false});
const page=await context.newPage();
try {
  const response=await page.goto((process.env.QA_ORIGIN||'http://127.0.0.1:4173')+'/editoriales/');
  assert.equal(response.status(),200);
  const cards=page.locator('[data-editorial-card]');
  const total=await cards.count();
  assert.ok(total>=100,'El directorio debe conservar el contenido estático');
  assert.equal(await cards.locator(':scope[hidden]').count(),0,'No debe haber fichas ocultas');
  for(const selector of ['[data-editoriales-search]','[data-editoriales-genre]','[data-editoriales-status]','[data-editoriales-country]','[data-editoriales-sort]','[data-editoriales-direct]','[data-editoriales-reset]']) {
    const control=page.locator(selector);
    if(await control.isVisible()) assert.equal(await control.isDisabled(),true,selector+' aparenta funcionar sin JavaScript');
  }
  const links=await cards.locator('h2 a').evaluateAll(nodes=>nodes.map(a=>a.getAttribute('href')));
  assert.equal(links.length,total);
  assert.ok(links.every(h=>h?.startsWith('/editoriales/')));
  console.log('PASS no-JS editorial directory');
} finally {await context.close();await browser.close();}
