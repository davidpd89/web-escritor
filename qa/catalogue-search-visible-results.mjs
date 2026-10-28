import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=(process.env.QA_ORIGIN||process.env.SITE_BASE_URL||'http://127.0.0.1:4173').replace(/\/$/,'');
const route='/recomendaciones/';
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try {
  const page=await browser.newPage();
  const response=await page.goto(BASE+route,{waitUntil:'domcontentloaded'});
  assert.equal(response?.status(),200,`${route}: HTTP incorrecto`);
  const input=page.locator('[data-catalogue-filters] [data-filter="q"]');
  assert.equal(await input.count(),1,`${route}: buscador no encontrado`);
  const cards=page.locator('[data-reading-catalogue] [data-catalogue-book]');
  assert.ok(await cards.count()>1,`${route}: catálogo insuficiente`);
  const target=await cards.first().getAttribute('data-title');
  assert.ok(target?.trim(),`${route}: primera ficha sin título`);
  await input.fill(target);
  await page.waitForFunction(()=>{
    const input=document.querySelector('[data-filter="q"]');
    const cards=[...document.querySelectorAll('[data-catalogue-book]')];
    const visible=cards.filter(c=>!c.hidden);
    return input.value&&visible.length>0&&visible.every(c=>c.dataset.search?.toLocaleLowerCase('es').includes(input.value.toLocaleLowerCase('es')));
  });
  const result=await page.evaluate(()=>{
    const cards=[...document.querySelectorAll('[data-catalogue-book]')];
    const visible=cards.filter(c=>!c.hidden);
    return {count:visible.length,titles:visible.map(c=>c.dataset.title),images:visible.map(c=>!!c.querySelector('img')),status:document.querySelector('[data-catalogue-count]')?.textContent||''};
  });
  assert.ok(result.titles.includes(target),`${route}: búsqueda de ${target} no devuelve su ficha`);
  assert.ok(result.images.every(Boolean),`${route}: resultado sin imagen de cubierta`);
  assert.ok(result.status.includes(String(result.count)),`${route}: contador ${result.status} no refleja ${result.count} resultados`);
} finally {await browser.close();}
console.log('PASS catalogue-search-visible-results');