import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=process.env.QA_BASE_URL||process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
const failures=[];
try {
  for(const width of [320,390,768,1280]) {
    const context=await browser.newContext({viewport:{width,height:900}});
    const page=await context.newPage();
    try {
      await page.goto(BASE+'/editoriales/',{waitUntil:'domcontentloaded'});
      const search=page.locator('[data-editoriales-search]');
      await search.fill('Minotauro');
      const cards=page.locator('[data-editorial-card]:visible');
      assert.equal(await cards.count(),1,`${width}: búsqueda no produce un único resultado`);
      const link=cards.first().locator('h2 a[href]');
      const href=await link.getAttribute('href');
      assert.ok(href?.startsWith('/editoriales/'),`${width}: destino inválido`);
      await link.focus();
      assert.equal(await link.evaluate(el=>document.activeElement===el),true,`${width}: enlace no enfocable`);
      await page.keyboard.press('Enter');
      await page.waitForURL(url=>url.pathname===href);
      const keyboardTitle=(await page.locator('main h1').first().innerText()).trim();
      await page.goto(BASE+'/editoriales/',{waitUntil:'domcontentloaded'});
      await page.locator('[data-editoriales-search]').fill('Minotauro');
      await page.locator('[data-editorial-card]:visible h2 a').click();
      await page.waitForURL(url=>url.pathname===href);
      const pointerTitle=(await page.locator('main h1').first().innerText()).trim();
      assert.equal(pointerTitle,keyboardTitle,`${width}: destinos con identidad distinta`);
      assert.equal(pointerTitle,'Minotauro',`${width}: expediente incorrecto`);
    } catch(e){failures.push(`${width}: ${e.message}`);}
    finally{await context.close();}
  }
}finally{await browser.close();}
assert.deepEqual(failures,[],failures.join('\n'));
console.log('PASS equivalencia teclado/ratón en directorio editorial');
