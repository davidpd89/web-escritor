import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch();
const page = await browser.newPage();

async function search(query) {
  await page.locator('[data-editoriales-search]').fill(query);
  return (await page.locator('[data-editorial-card]:visible').evaluateAll(cards=>cards.map(c=>c.dataset.name))).sort();
}

try {
  const response = await page.goto(BASE+'/editoriales/',{waitUntil:'domcontentloaded'});
  assert.ok(response?.ok());
  const groups = [
    ['fantasía','fantasia','FANTASÍA','fantasi\u0301a'],
    ['ficción','ficcion','FICCIÓN','ficcio\u0301n'],
    ['poesía','poesia','POESÍA','poesi\u0301a'],
    ['México','mexico','MÉXICO','Me\u0301xico']
  ];
  for(const group of groups) {
    const baseline = await search(group[0]);
    assert.ok(baseline.length>0,`Fixture sin resultados: ${group[0]}`);
    for(const variant of group.slice(1)) {
      assert.deepEqual(await search(variant),baseline,`Normalización de ${variant}`);
    }
  }
  const enie = await search('ñ');
  const ene = await search('n');
  assert.notDeepEqual(enie,ene,'La búsqueda debe distinguir ñ de n');
  await page.locator('[data-editoriales-reset]').click();
  assert.equal(await page.locator('[data-editoriales-search]').inputValue(),'');
  console.log('PASS editoriales linguistic search matrix');
} finally {
  await browser.close();
}
