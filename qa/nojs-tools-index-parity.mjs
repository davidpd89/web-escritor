import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const O=(process.env.QA_ORIGIN||'http://127.0.0.1:4173').replace(/\/$/,'');
const browser=await chromium.launch({headless:true});
try{
  const context=await browser.newContext({javaScriptEnabled:false});
  await context.route('**/*',r=>r.request().url().startsWith(O+'/')?r.continue():r.abort());
  const page=await context.newPage();
  await page.goto(O+'/herramientas/',{waitUntil:'domcontentloaded'});
  const links=await page.locator('main noscript .samuel-route-list a[href]').evaluateAll(nodes=>nodes.map(a=>a.getAttribute('href')));
  assert.ok(links.length>=15,'Fallback de herramientas incompleto');
  assert.equal(new Set(links).size,links.length,'Rutas duplicadas');
  const cards=await page.locator('[data-tool]').count();
  assert.ok(cards>=links.length,'Fallback mayor que catálogo real');
  const cardLinks=await page.locator('[data-tool] h3 a[href]').evaluateAll(nodes=>nodes.map(a=>a.getAttribute('href')));
  assert.equal(cardLinks.length,cards,'Tarjetas sin enlace principal');
  assert.deepEqual([...links].sort(),[...cardLinks].sort(),'El fallback noscript no coincide con las tarjetas');
  for(const href of links){
    assert.ok(/^\/(?!\/)[a-zA-Z0-9/_-]+\/$/.test(href),href+': ruta local incorrecta');
    const response=await context.request.get(O+href);
    assert.equal(response.status(),200,href+': enlace roto');
    assert.match((await response.text()).slice(0,400),/<!doctype html/i,href+': destino no HTML');
  }
  await context.close();
}finally{await browser.close();}
console.log('PASS nojs tools index parity');