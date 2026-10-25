import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=process.env.QA_BASE_URL||'http://127.0.0.1:4173';
const cases=[
  {section:'#las-manecillas-del-recuerdo',href:'/las-manecillas-del-recuerdo/'},
  {section:'#obra-publicada',href:'/libros/samuel-entre-mundos/'}
];
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try {
  for(const width of [390,768,1440]){
    const context=await browser.newContext({viewport:{width,height:900}});
    const page=await context.newPage();
    for(const test of cases){
      await page.goto(BASE+'/libros/',{waitUntil:'load'});
      const action=page.locator(`main ${test.section} .books-stage__actions a[href="${test.href}"]`);
      assert.equal(await action.count(),1,'Acción editorial única');
      await action.scrollIntoViewIfNeeded();
      await action.click();
      await page.waitForURL(url=>url.pathname===test.href);
      assert.equal(await page.locator('main h1').count(),1);
      await page.goBack({waitUntil:'load'});
      assert.equal(new URL(page.url()).pathname,'/libros/');
      assert.equal(await page.locator(`main ${test.section}`).count(),1);
      assert.equal(await action.isVisible(),true);
      await action.click();
      assert.equal(new URL(page.url()).pathname,test.href,'Segunda navegación conserva el destino');
    }
    await context.close();
  }
}finally{await browser.close();}
console.log('libros-history-journey: OK');