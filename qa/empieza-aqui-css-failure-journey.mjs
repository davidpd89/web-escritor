import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const ORIGIN=(process.env.QA_ORIGIN||'http://127.0.0.1:4173').replace(/\/$/,'');
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try{
  const context=await browser.newContext({viewport:{width:390,height:844}});
  await context.route('**/*.css*',route=>route.abort('failed'));
  const page=await context.newPage();
  const response=await page.goto(`${ORIGIN}/empieza-aqui/`,{waitUntil:'load'});
  assert(response?.ok(),`/empieza-aqui/: HTTP ${response?.status()}`);
  const entries=page.locator('main .findability-entry');
  assert.equal(await entries.count(),7,'/empieza-aqui/: faltan entradas de orientación sin CSS');
  for(let i=0;i<7;i++){
    const entry=entries.nth(i);
    assert(await entry.locator('h2').isVisible(),`/empieza-aqui/: entrada ${i+1} sin encabezado visible`);
    assert(await entry.locator('a[href]').count()>0,`/empieza-aqui/: entrada ${i+1} sin destinos`);
  }
  for(const destination of ['/las-manecillas-del-recuerdo/','/las-manecillas-del-recuerdo/kindle/']){
    await page.goto(`${ORIGIN}/empieza-aqui/`,{waitUntil:'load'});
    const link=page.locator('main .findability-entry a[href]').filter({has:page.locator('span.__never__')});
    const target=page.locator(`main .findability-entry a[href='${destination}']`).first();
    assert(await target.isVisible(),`/empieza-aqui/: enlace ${destination} invisible sin CSS`);
    await target.click();
    assert.equal(new URL(page.url()).pathname,destination,`/empieza-aqui/: navegación incorrecta hacia ${destination}`);
    assert(await page.locator('main').count()>0,`${destination}: destino sin contenido principal`);
  }
  console.log('Empieza aquí: rutas principales operativas sin CSS');
}finally{await browser.close();}