import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const O=(process.env.QA_ORIGIN||'http://127.0.0.1:4173').replace(/\/$/,'');
const browser=await chromium.launch({headless:true});
try{
  const context=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844}});
  await context.route('**/*',r=>r.request().url().startsWith(O+'/')?r.continue():r.abort());
  const page=await context.newPage();
  await page.goto(O+'/convocatorias-escritores/',{waitUntil:'domcontentloaded'});
  const records=await page.locator('[data-radar-item]').evaluateAll(nodes=>nodes.map(el=>({name:el.querySelector('h2')?.textContent?.trim(),date:el.querySelector('time[datetime]')?.getAttribute('datetime'),source:el.querySelector('a[data-radar-source]')?.href,visible:!!el.getClientRects().length&&getComputedStyle(el).visibility!=='hidden'})));
  assert.ok(records.length>=5,'Radar sin registros');
  for(const r of records){
    assert.ok(r.name,r.name+': sin título');
    assert.ok(r.date||r.name.toLowerCase().includes('sin fecha'),r.name+': sin fecha o explicación');
    assert.ok(/^https?:\/\//.test(r.source||''),r.name+': fuente inaccesible');
    assert.ok(r.visible,r.name+': ficha oculta sin JavaScript');
  }
  const href=await page.locator('[data-radar-calendar]').getAttribute('href');
  assert.match(href||'',/\.ics$/);
  const response=await context.request.get(O+href);
  assert.equal(response.status(),200,'Calendario inaccesible');
  assert.match(await response.text(),/BEGIN:VCALENDAR/);
  await context.close();
}finally{await browser.close();}
console.log('PASS nojs radar sources and calendar');