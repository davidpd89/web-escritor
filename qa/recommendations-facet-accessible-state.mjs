import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const BASE=process.env.RECOMMENDATIONS_BASE_URL||'http://127.0.0.1:4173';
const browser=await chromium.launch();
try{
 const page=await browser.newPage();
 await page.route(/^https?:\/\//,r=>new URL(r.request().url()).origin===new URL(BASE).origin?r.continue():r.abort());
 await page.goto(BASE+'/recomendaciones/');
 const groups=page.locator('details[data-facet-group]');
 assert.ok(await groups.count()>0);
 for(let i=0;i<await groups.count();i++){
  const group=groups.nth(i);
  await group.evaluate(el=>el.open=true);
  const boxes=group.locator('input[type="checkbox"][data-facet]');
  for(let j=0;j<await boxes.count();j++){
   const box=boxes.nth(j);
   if(await box.isDisabled()||!await box.isVisible())continue;
   const label=await box.evaluate(el=>el.closest('label')?.innerText.trim());
   assert.ok(label,`Filtro sin nombre: grupo ${i}, opción ${j}`);
   await box.check();
   assert.ok(await box.isChecked());
   assert.ok(await box.isVisible(),'Filtro seleccionado oculto');
   assert.ok(await box.isEnabled(),'Filtro seleccionado deshabilitado');
   await box.uncheck();
   assert.ok(!await box.isChecked());
  }
 }
 console.log('PASS facet accessible state');
}finally{await browser.close();}