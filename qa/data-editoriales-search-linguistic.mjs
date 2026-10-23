import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright';

const ORIGIN=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const data=JSON.parse(fs.readFileSync('editoriales/editoriales-data.json','utf8')).publishers;
const browser=await chromium.launch({headless:true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});
try {
  const page=await browser.newPage();
  assert.equal((await page.goto(ORIGIN+'/editoriales/',{waitUntil:'networkidle'})).status(),200);
  const search=page.locator('[data-editoriales-search]');
  const visible=()=>page.locator('[data-editorial-card]:visible').evaluateAll(nodes=>nodes.map(n=>n.dataset.name).sort());
  assert.equal((await visible()).length,data.length);
  const probes=data.filter(x=>/^[A-Za-z ]+$/.test(x.name)).slice(0,8);
  assert.ok(probes.length>=2,'Sin muestras para equivalencia lingüística');
  for(const record of probes){
    await search.fill(record.name);
    const base=await visible();
    assert.ok(base.length>=1,record.name);
    for(const term of [record.name.toUpperCase(),record.name.toLowerCase(),'  '+record.name+'  ']){
      await search.fill(term);
      assert.deepEqual(await visible(),base,`Búsqueda divergente: ${term}`);
    }
  }
  await page.locator('[data-editoriales-reset]').click();
  assert.equal((await visible()).length,data.length);
  assert.equal(await search.inputValue(),'');
} finally {
  await browser.close();
}
console.log('OK: equivalencia de búsqueda de editoriales');
