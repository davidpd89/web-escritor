import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const O=(process.env.QA_ORIGIN||'http://127.0.0.1:4173').replace(/\/$/,'');
const browser=await chromium.launch({headless:true});
try{
  const context=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844}});
  await context.route('**/*',r=>r.request().url().startsWith(O+'/')?r.continue():r.abort());
  const page=await context.newPage();
  await page.goto(O+'/asistente/',{waitUntil:'domcontentloaded'});
  const state=await page.evaluate(()=>({notice:[...document.querySelectorAll('main noscript')].filter(e=>e.getClientRects().length).map(e=>e.textContent).join(' '),query:document.querySelector('[data-assistant-query]'),form:document.querySelector('[data-assistant-form]'),map:[...document.querySelectorAll('main a[href="/mapa-del-sitio/"]')].some(a=>a.getClientRects().length)}));
  assert.ok(state.map,'No hay ruta alternativa al mapa');
  assert.match(state.notice,/javascript|scripts/i,'Falta advertencia explícita sin JavaScript');
  assert.match(state.notice,/buscar|pregunta|asistente|funcionar/i,'Advertencia sin explicación del comportamiento');
  const enabled=await page.locator('[data-assistant-submit]:visible:not(:disabled)').count();
  assert.equal(enabled,0,'Enviar pregunta permanece activo cuando no puede funcionar');
  await context.close();
}finally{await browser.close();}
console.log('PASS nojs assistant honest degradation');