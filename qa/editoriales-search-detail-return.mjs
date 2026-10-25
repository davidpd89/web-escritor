import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=process.env.QA_BASE_URL||process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
const failures=[];
try {
  for(const viewport of [{width:390,height:844},{width:1280,height:900}]) {
    const context=await browser.newContext({viewport});
    const page=await context.newPage();
    try {
      await page.goto(BASE+'/editoriales/',{waitUntil:'domcontentloaded'});
      const search=page.locator('[data-editoriales-search]');
      await search.fill('Minotauro');
      const result=page.locator('[data-editorial-card]:visible');
      assert.equal(await result.count(),1,'La consulta no identifica un único expediente');
      const href=await result.locator('h2 a').getAttribute('href');
      await result.locator('h2 a').click();
      await page.waitForURL(url=>url.pathname===href);
      assert.equal((await page.locator('main h1').first().innerText()).trim(),'Minotauro');
      await page.goBack({waitUntil:'domcontentloaded'});
      assert.equal(new URL(page.url()).pathname,'/editoriales/');
      assert.equal(await page.locator('[data-editoriales-search]').inputValue(),'Minotauro','Se pierde la consulta al regresar');
      assert.equal(await page.locator('[data-editorial-card]:visible').count(),1,'Se pierde el resultado filtrado');
      assert.equal(await page.locator('[data-editorial-card]:visible h2 a').getAttribute('href'),href,'El resultado cambia de destino');
    }catch(e){failures.push(`${viewport.width}: ${e.message}`);}
    finally{await context.close();}
  }
}finally{await browser.close();}
assert.deepEqual(failures,[],failures.join('\n'));
console.log('PASS recorrido de búsqueda, detalle y retorno');
