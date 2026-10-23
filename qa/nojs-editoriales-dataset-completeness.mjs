import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright';
const O=(process.env.QA_ORIGIN||'http://127.0.0.1:4173').replace(/\/$/,'');
const dataset=JSON.parse(fs.readFileSync('editoriales/editoriales-data.json','utf8')).publishers;
assert.ok(Array.isArray(dataset)&&dataset.length>0,'Dataset vacío');
const browser=await chromium.launch({headless:true});
try{
  const context=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844}});
  await context.route('**/*',r=>r.request().url().startsWith(O+'/')?r.continue():r.abort());
  const page=await context.newPage();
  await page.goto(O+'/editoriales/',{waitUntil:'domcontentloaded'});
  const cards=await page.locator('[data-editorial-card]').evaluateAll(nodes=>nodes.map(el=>({name:el.dataset.name,status:el.dataset.status,visible:!!el.getClientRects().length&&getComputedStyle(el).visibility!=='hidden',link:el.querySelector('h2 a')?.getAttribute('href'),description:el.querySelector('p')?.textContent?.trim()})));
  assert.equal(cards.length,dataset.length,'No hay paridad dataset/HTML');
  assert.equal(new Set(cards.map(x=>x.name)).size,cards.length,'Nombres duplicados');
  for(const card of cards){
    assert.ok(card.visible,card.name+': ficha oculta sin JS');
    assert.ok(card.link?.startsWith('/editoriales/'),card.name+': ficha inaccesible');
    assert.ok(card.description?.length>20,card.name+': sin descripción');
    assert.ok(card.status,card.name+': estado ausente');
  }
  await context.close();
}finally{await browser.close();}
console.log('PASS nojs editoriales dataset: '+dataset.length);