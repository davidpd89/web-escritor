import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const O=(process.env.QA_ORIGIN||'http://127.0.0.1:4173').replace(/\/$/,'');
const browser=await chromium.launch({headless:true});
const snapshot=page=>page.locator('[data-catalogue-book]').evaluateAll(nodes=>nodes.map(el=>({id:el.dataset.bookId,detail:el.querySelector('.catalogue-card__cover')?.getAttribute('href'),buys:[...el.querySelectorAll('a[href]')].map(a=>a.getAttribute('href')).filter(h=>/amazon|amzn/i.test(h||''))})).sort((a,b)=>a.id.localeCompare(b.id)));
try{
  const plain=await browser.newContext({javaScriptEnabled:false});
  await plain.route('**/*',r=>r.request().url().startsWith(O+'/')?r.continue():r.abort());
  const p1=await plain.newPage();
  await p1.goto(O+'/recomendaciones/',{waitUntil:'load'});
  const baseline=await snapshot(p1);
  await plain.close();
  const enhanced=await browser.newContext();
  await enhanced.route('**/*',r=>{const u=r.request().url();if(u.startsWith(O+'/assets/reading-market.json'))return r.abort();return u.startsWith(O+'/')?r.continue():r.abort();});
  const p2=await enhanced.newPage();
  await p2.goto(O+'/recomendaciones/',{waitUntil:'load'});
  const actual=await snapshot(p2);
  assert.deepEqual(actual,baseline,'La caída del mercado alteró fichas o URLs');
  assert.ok(actual.length>=20,'Catálogo vacío tras error');
  for(const card of actual)for(const href of card.buys)assert.ok(!/null|undefined/i.test(href),card.id+': compra inválida');
  await enhanced.close();
}finally{await browser.close();}
console.log('PASS market fetch failure static CTA');