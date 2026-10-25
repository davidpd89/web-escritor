import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE=process.env.QA_BASE_URL||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true});
try {
  const page=await browser.newPage();
  const response=await page.goto(BASE+'/cuaderno/');
  assert.equal(response.status(),200);
  const inventory=await page.evaluate(()=>{
    const entries=[...document.querySelectorAll('.cuaderno-ledger > .cuaderno-entry')];
    const featured=document.querySelector('.cuaderno-feature');
    const count=Number(document.querySelector('.cuaderno-masthead__folio strong')?.textContent.trim());
    const items=[featured,...entries].filter(Boolean).map(el=>({
      index:el.querySelector('.cuaderno-feature__index,.cuaderno-entry__index')?.textContent.trim(),
      href:el.querySelector('h2 a,h3 a')?.getAttribute('href'),
      title:el.querySelector('h2,h3')?.textContent.trim()
    }));
    return {count,items};
  });
  assert.ok(inventory.items.length>0,'inventario vacío');
  assert.equal(inventory.count,inventory.items.length,'contador editorial desactualizado');
  const hrefs=new Set();
  for(let i=0;i<inventory.items.length;i++){
    const item=inventory.items[i];
    assert.ok(item.title&&item.href,'entrada incompleta');
    assert.ok(!hrefs.has(item.href),`destino duplicado: ${item.href}`);
    hrefs.add(item.href);
    const ordinal=Number(item.index?.split('/')[0].trim());
    assert.equal(ordinal,i+1,`ordinal incorrecto: ${item.href}`);
    const url=new URL(item.href,BASE);
    assert.equal(url.origin,new URL(BASE).origin,'destino fuera del sitio');
    const target=await page.request.get(url.href);
    assert.equal(target.status(),200,`destino no publicado: ${item.href}`);
    assert.match(target.headers()['content-type']||'',/text\/html/,`destino no HTML: ${item.href}`);
  }
  console.log('PASS cuaderno inventory');
}finally{await browser.close();}
