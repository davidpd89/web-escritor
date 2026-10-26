import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=(process.env.QA_ORIGIN||process.env.SITE_BASE_URL||'http://127.0.0.1:4173').replace(/\/$/,'');
const route='/recomendaciones/';
const browser=await chromium.launch({headless:true});
try {
  const page=await browser.newPage();
  await page.goto(BASE+route,{waitUntil:'domcontentloaded'});
  const input=page.locator('[data-filter="q"]');
  const cards=page.locator('[data-catalogue-book]');
  const total=await cards.count();
  assert.ok(total>0,`${route}: catálogo sin fichas`);
  const query='zzzzzzzzzzzzzzzzzzzzzzzz';
  await input.fill(query);
  await page.waitForFunction(()=>document.querySelector('[data-catalogue-count]')?.textContent?.includes('0 libros'));
  assert.equal(await cards.locator('visible=true').count(),0,`${route}: aparecen fichas para ${query}`);
  assert.equal(await page.locator('[data-catalogue-empty]').isVisible(),true,`${route}: estado vacío no visible`);
  await input.fill('');
  await page.waitForFunction(()=>document.querySelector('[data-catalogue-count]')?.textContent?.match(/^[1-9]\d* libros?/));
  assert.equal(await page.locator('[data-catalogue-empty]').isVisible(),false,`${route}: estado vacío permanece tras limpiar`);
  const restored=await page.evaluate(()=>[...document.querySelectorAll('[data-catalogue-book]')].filter(c=>!c.hidden).map(c=>({title:c.dataset.title,image:!!c.querySelector('img')})));
  assert.ok(restored.length>0,`${route}: no se recuperaron resultados`);
  assert.ok(restored.every(c=>c.image),`${route}: alguna ficha recuperada carece de portada`);
  assert.equal(new URL(page.url()).hash,'',`${route}: URL conserva la búsqueda borrada`);
} finally {await browser.close();}
console.log('PASS catalogue-empty-search-recovery');