import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=(process.env.QA_ORIGIN||process.env.SITE_BASE_URL||'http://127.0.0.1:4173').replace(/\/$/,'');
const route='/recomendaciones/';
const browser=await chromium.launch({headless:true});
const snapshot=page=>page.evaluate(()=>({cards:[...document.querySelectorAll('[data-catalogue-book]')].filter(c=>!c.hidden).map(c=>({id:c.dataset.bookId,src:c.querySelector('img')?.getAttribute('src')})),count:document.querySelector('[data-catalogue-count]')?.textContent}));
try {
  const page=await browser.newPage();
  await page.goto(BASE+route,{waitUntil:'domcontentloaded'});
  const initial=await snapshot(page);
  assert.ok(initial.cards.length>0,`${route}: catálogo inicialmente vacío`);
  const search=page.locator('[data-filter="q"]');
  await search.fill(initial.cards[0].id);
  await page.waitForFunction(()=>location.hash.includes('q='));
  const reset=page.locator('[data-catalogue-filters] [type="reset"]');
  assert.equal(await reset.count(),1,`${route}: botón de restablecimiento ausente`);
  await reset.click();
  await page.waitForFunction(()=>!document.querySelector('[data-filter="q"]')?.value&&!location.hash);
  const restored=await snapshot(page);
  assert.deepEqual(restored.cards,initial.cards,`${route}: fichas o portadas diferentes tras restablecer`);
  assert.equal(restored.count,initial.count,`${route}: contador diferente tras restablecer`);
  assert.equal(new URL(page.url()).hash,'',`${route}: URL conserva filtros anteriores`);
} finally {await browser.close();}
console.log('PASS catalogue-filter-reset-parity');