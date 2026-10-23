import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const O=(process.env.QA_ORIGIN||'http://127.0.0.1:4173').replace(/\/$/,'');
const browser=await chromium.launch({headless:true});
try{
  const context=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844}});
  await context.route('**/*',r=>r.request().url().startsWith(O+'/')?r.continue():r.abort());
  const page=await context.newPage();
  await page.goto(O+'/recomendaciones/',{waitUntil:'domcontentloaded'});
  const cards=await page.locator('[data-catalogue-book]').evaluateAll(nodes=>nodes.map(el=>({visible:!!el.getClientRects().length&&getComputedStyle(el).visibility!=='hidden',id:el.dataset.bookId,detail:el.querySelector('.catalogue-card__cover')?.getAttribute('href'),links:[...el.querySelectorAll('a[href]')].map(a=>a.getAttribute('href'))})));
  assert.ok(cards.length>=20,'Catálogo demasiado pequeño');
  assert.equal(cards.filter(x=>x.visible).length,cards.length,'Fichas ocultas sin JS');
  assert.equal(new Set(cards.map(x=>x.id)).size,cards.length,'IDs duplicados');
  for(const card of cards){
    assert.ok(card.detail?.startsWith('/recomendaciones/libros/'),card.id+': ficha no accesible');
    assert.ok(card.links.length>0,card.id+': sin enlaces');
    for(const href of card.links) assert.ok(href&&!/^(?:null|undefined|#|javascript:)/i.test(href),card.id+': enlace inválido '+href);
  }
  assert.equal(await page.locator('[data-catalogue-empty]:visible').count(),0,'Estado vacío visible con catálogo completo');
  await context.close();
}finally{await browser.close();}
console.log('PASS nojs reading commerce fallback');