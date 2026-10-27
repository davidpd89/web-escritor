import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=(process.env.QA_ORIGIN||process.env.SITE_BASE_URL||'http://127.0.0.1:4173').replace(/\/$/,'');
const route='/recomendaciones/';
const browser=await chromium.launch({headless:true});
const snapshot=page=>page.evaluate(()=>[...document.querySelectorAll('[data-catalogue-book]')].filter(c=>!c.hidden).map(c=>({id:c.dataset.bookId,cover:c.querySelector('img')?.getAttribute('src')||''})));
try {
  const context=await browser.newContext();
  const first=await context.newPage();
  await first.goto(BASE+route,{waitUntil:'domcontentloaded'});
  await first.waitForFunction(()=>document.querySelector('[data-catalogue-pagination] button:not([disabled])'));
  const initial=await snapshot(first);
  const next=first.locator('[data-catalogue-pagination] button').filter({hasText:'Siguiente'});
  await next.click();
  await first.waitForFunction(()=>new URLSearchParams(location.hash.slice(1)).get('pagina')==='2');
  const expected=await snapshot(first);
  assert.ok(expected.length>0,`${route}: segunda página vacía`);
  assert.ok(expected.every(x=>x.id&&x.cover),`${route}: segunda página con identificadores o portadas ausentes`);
  assert.ok(!expected.some(x=>initial.some(y=>y.id===x.id)),`${route}: libros repetidos entre páginas`);
  const shared=first.url();
  const second=await context.newPage();
  await second.goto(shared,{waitUntil:'domcontentloaded'});
  await second.waitForFunction(()=>document.querySelector('[data-catalogue-pagination]')?.textContent?.includes('Página 2'));
  assert.deepEqual(await snapshot(second),expected,`${route}: URL ${shared} no recupera las mismas cubiertas`);
  await context.close();
} finally {await browser.close();}
console.log('PASS catalogue-pagination-shareable-url');