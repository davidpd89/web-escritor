import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const O=(process.env.QA_ORIGIN||'http://127.0.0.1:4173').replace(/\/$/,'');
const CASES=[['/editoriales/','[data-editoriales-search]'],['/convocatorias-escritores/','[data-radar-search]'],['/recomendaciones/','[data-catalogue-filters]'],['/herramientas/','[data-filter]'],['/asistente/','[data-assistant-query]']];
const browser=await chromium.launch({headless:true});
const failures=[];
try {
  const context=await browser.newContext({javaScriptEnabled:false});
  await context.route('**/*',r=>r.request().url().startsWith(O+'/')?r.continue():r.abort());
  const page=await context.newPage();
  for(const [url,control] of CASES){
    await page.goto(O+url,{waitUntil:'domcontentloaded'});
    try {
      assert.ok(await page.locator(control).count(),url+': falta control de referencia');
      const explanation=await page.evaluate(()=>[...document.querySelectorAll('main noscript')].filter(n=>n.getClientRects().length&&getComputedStyle(n).visibility!=='hidden').map(n=>n.textContent).join(' '));
      assert.match(explanation,/javascript|scripts/i,url+': falta explicación sin JS');
      assert.match(explanation,/filtro|búsqueda|buscar|herramienta|asistente|funcionar|activar|requiere/i,url+': explicación no específica');
    }catch(e){failures.push(e.message);}
  }
  await context.close();
}finally{await browser.close();}
assert.deepEqual(failures,[],failures.join('\n'));
console.log('PASS nojs controls affordance');