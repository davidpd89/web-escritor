import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const route='/empieza-aqui/';
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try {
  for(const js of [true,false]) {
    const context=await browser.newContext({javaScriptEnabled:js});
    const page=await context.newPage();
    await page.goto(`${ORIGIN}${route}`,{waitUntil:'load'});
    const result=await page.evaluate(()=>{
      const list=document.querySelector('main ol.findability-index');
      if(!list)return null;
      return {name:list.getAttribute('aria-label'),items:[...list.children].filter(el=>el.matches('li')).map(li=>({id:li.id,headings:[...li.querySelectorAll('h2,h3')].map(h=>({level:Number(h.tagName[1]),text:h.textContent.trim()})),links:[...li.querySelectorAll('a[href]')].filter(a=>a.getClientRects().length).length}))};
    });
    assert(result,`${route} JS=${js}: falta la lista semántica`);
    assert(result.name?.trim(),`${route} JS=${js}: lista sin nombre accesible`);
    assert.equal(result.items.length,7,`${route} JS=${js}: número de rutas ${result.items.length}`);
    for(const [i,item] of result.items.entries()) {
      assert(item.id,`${route} JS=${js}: ruta ${i+1} sin identificador`);
      assert.equal(item.headings[0]?.level,2,`${route} JS=${js}: ruta ${item.id} sin H2 inicial`);
      assert(item.headings[0].text,`${route} JS=${js}: ruta ${item.id} con H2 vacío`);
      assert.equal(item.headings.filter(h=>h.level===2).length,1,`${route} JS=${js}: ruta ${item.id} con encabezados principales ambiguos`);
      assert(item.headings.every(h=>h.text),`${route} JS=${js}: ruta ${item.id} con encabezado vacío`);
      assert(item.links>0,`${route} JS=${js}: ruta ${item.id} sin acción navegable`);
    }
    await context.close();
  }
  console.log('empieza-aqui-semantic-routes-regression: OK');
} finally {await browser.close();}
