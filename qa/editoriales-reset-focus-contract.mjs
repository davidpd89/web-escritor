import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE=process.env.QA_BASE_URL||process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try {
 const page=await browser.newPage();
 const response=await page.goto(`${BASE}/editoriales/`,{waitUntil:'domcontentloaded'});
 assert.ok(response?.ok(),'/editoriales/: error HTTP');
 const total=await page.locator('[data-editorial-card]').count();
 assert.ok(total>0,'/editoriales/: directorio vacío');
 const search=page.locator('[data-editoriales-search]');
 await search.fill('Minotauro');
 await page.waitForFunction(n=>[...document.querySelectorAll('[data-editorial-card]')].filter(el=>!el.hidden).length<n,total);
 await page.locator('[data-editoriales-direct]').check();
 await page.locator('[data-editoriales-reset]').click();
 await page.waitForFunction(n=>[...document.querySelectorAll('[data-editorial-card]')].filter(el=>!el.hidden).length===n,total);
 assert.equal(await search.inputValue(),'','/editoriales/: búsqueda no limpiada');
 assert.equal(await search.evaluate(el=>document.activeElement===el),true,'/editoriales/: Limpiar no devuelve el foco al buscador');
 assert.equal(await page.locator('[data-editoriales-direct]').isChecked(),false,'/editoriales/: envío directo sigue activo');
 assert.equal(await page.locator('[data-editoriales-search]').count(),1,'/editoriales/: buscador duplicado');
 assert.equal(await search.evaluate(el=>el.labels?.[0]?.textContent.trim()),'Buscar','/editoriales/: nombre accesible del buscador incorrecto');
} finally {await browser.close();}
