import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({headless:true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});
try {
  const page = await browser.newPage({viewport:{width:390,height:900}});
  const response = await page.goto(ORIGIN + '/recursos/herramientas-para-escritores/', {waitUntil:'networkidle'});
  assert.equal(response.status(), 200);
  const search = page.locator('[data-wt-search]');
  const cards = page.locator('.wt-card');
  const initial = await cards.count();
  assert.ok(initial >= 3);
  const visible = () => page.locator('.wt-card:visible').evaluateAll(nodes=>nodes.map(n=>n.dataset.name).sort());
  const values = await cards.evaluateAll(nodes=>nodes.map(n=>({name:n.dataset.name,stages:n.dataset.stages.split(' ')})));
  const term = values[0].name;
  await search.fill(term);
  const direct = await visible();
  assert.deepEqual(direct, values.filter(x=>x.name.includes(term)).map(x=>x.name).sort());
  await search.fill('');
  await search.focus();
  await search.pressSequentially(term);
  assert.deepEqual(await visible(), direct, 'Teclado y entrada directa difieren');
  await page.locator('[data-wt-clear]').click();
  assert.equal(await search.evaluate(el=>document.activeElement===el), true);
  assert.equal((await visible()).length, initial);
  for (const stage of await page.locator('[data-wt-stage] option').evaluateAll(nodes=>nodes.map(n=>n.value).filter(Boolean))) {
    await page.locator('[data-wt-stage]').selectOption(stage);
    const expected = values.filter(x=>x.stages.includes(stage)).map(x=>x.name).sort();
    assert.deepEqual(await visible(), expected, stage);
    const count = await page.locator('[data-wt-count]').innerText();
    assert.ok(count.startsWith(String(expected.length) + ' '), stage);
  }
  await page.locator('[data-wt-clear]').click();
  assert.equal((await visible()).length, initial);
} finally {
  await browser.close();
}
console.log('OK: equivalencia de entrada en filtros de herramientas');
