import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const browser=await chromium.launch({headless:true});
const page=await browser.newPage();
const collator=new Intl.Collator('es',{sensitivity:'base'});
try {
  await page.goto((process.env.QA_ORIGIN||'http://127.0.0.1:4173')+'/editoriales/');
  const sort=page.locator('[data-editoriales-sort]');
  const cards=()=>page.locator('[data-editorial-card]').evaluateAll(nodes=>nodes.map(n=>({name:n.dataset.name,date:n.dataset.verifiedAt})));
  await sort.selectOption('recent');
  const recent=await cards();
  assert.ok(recent.length>=100,'El test debe abarcar el directorio, no una muestra');
  for(let i=1;i<recent.length;i++) {
    const a=recent[i-1],b=recent[i];
    assert.ok(a.date>=b.date,'Fechas desordenadas: '+a.name+' / '+b.name);
    if(a.date===b.date) assert.ok(collator.compare(a.name,b.name)<=0,'Empate inestable');
  }
  await sort.selectOption('name');
  const named=await cards();
  for(let i=1;i<named.length;i++) assert.ok(collator.compare(named[i-1].name,named[i].name)<=0,'Orden alfabético incorrecto');
  await sort.selectOption('recent');
  assert.deepEqual(await cards(),recent,'La ordenación debe ser reproducible');
  console.log('PASS monotonic sorting');
} finally {await browser.close();}
