import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright';

const ORIGIN=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const data=JSON.parse(fs.readFileSync('data/reading-catalogue.json','utf8'));
const published=new Set(data.libros.filter(b=>b.estado==='publicado').map(b=>b.id));
const browser=await chromium.launch({headless:true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});
try {
  const page=await browser.newPage({viewport:{width:390,height:900}});
  assert.equal((await page.goto(ORIGIN+'/recomendaciones/',{waitUntil:'networkidle'})).status(),200);
  const relations=data.libro_categorias.filter(r=>published.has(r.libro_id));
  const options=await page.locator('input[data-facet]').evaluateAll(nodes=>nodes.map(n=>({value:n.value,facet:n.dataset.facet,disabled:n.disabled})));
  const probe=options.find(o=>!o.disabled&&relations.filter(r=>r.categoria_id===o.value).length>0&&relations.filter(r=>r.categoria_id===o.value).length<=24);
  assert.ok(probe,'Falta una categoría acotada para prueba');
  const box=page.locator(`input[data-facet="${probe.facet}"][value="${probe.value}"]`);
  await box.check();
  const expected=new Set(relations.filter(r=>r.categoria_id===probe.value).map(r=>r.libro_id));
  const visible=()=>page.locator('[data-catalogue-book]:visible').evaluateAll(nodes=>nodes.map(n=>n.dataset.bookId).sort());
  const ids=await visible();
  assert.deepEqual(ids,[...expected].sort());
  assert.ok(page.url().includes(encodeURIComponent(probe.value)));
  await page.reload({waitUntil:'networkidle'});
  assert.equal(await box.isChecked(),true);
  assert.deepEqual(await visible(),ids,'Estado no restaurado desde hash');
  await box.uncheck();
  assert.ok((await visible()).length>=ids.length);
} finally {
  await browser.close();
}
console.log('OK: facetas, resultados y estado restaurable');
