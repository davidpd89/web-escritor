import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch();
const page = await browser.newPage();

const cases = [
  {genre:'fantasía',status:'',country:'',direct:false},
  {genre:'fantasía',status:'open',country:'España',direct:true},
  {genre:'romantasy',status:'',country:'',direct:false},
  {genre:'',status:'closed',country:'España',direct:false},
  {genre:'',status:'unknown',country:'',direct:false},
  {genre:'',status:'',country:'México',direct:true},
  {genre:'ciencia ficción',status:'open',country:'España',direct:false},
  {genre:'poesía',status:'',country:'Argentina',direct:false},
  {genre:'',status:'award_only',country:'',direct:true},
  {genre:'',status:'indirect',country:'',direct:false}
];

function norm(s) {
  return String(s).toLocaleLowerCase('es').normalize('NFD').replace(/(?<!n)\u0303|(?<!u)\u0308|[\u0300-\u0302\u0304-\u0307\u0309-\u036f]/g,'').normalize('NFC').trim();
}

try {
  const response = await page.goto(BASE + '/editoriales/', {waitUntil:'domcontentloaded'});
  assert.ok(response?.ok());
  const records = await page.locator('[data-editorial-card]').evaluateAll(cards => cards.map(c => ({name:c.dataset.name,genres:c.dataset.genres,country:c.dataset.country,status:c.dataset.status,direct:c.dataset.direct})));
  assert.ok(records.length >= 100, 'La prueba necesita el catálogo completo');
  const statusRegion = page.locator('[data-editoriales-count]');
  assert.equal(await statusRegion.getAttribute('role'),'status');
  assert.equal(await statusRegion.getAttribute('aria-live'),'polite');

  for (const item of cases) {
    await page.locator('[data-editoriales-reset]').click();
    if(item.genre) await page.locator('[data-editoriales-genre]').selectOption(item.genre);
    if(item.status) await page.locator('[data-editoriales-status]').selectOption(item.status);
    if(item.country) await page.locator('[data-editoriales-country]').selectOption(item.country);
    if(item.direct) await page.locator('[data-editoriales-direct]').check();

    const expected = records.filter(r =>
      (!item.genre || norm(r.genres).split('|').includes(norm(item.genre))) &&
      (!item.status || r.status === item.status) &&
      (!item.country || norm(r.country) === norm(item.country)) &&
      (!item.direct || r.direct === 'true')
    ).map(r => r.name).sort();
    const actual = (await page.locator('[data-editorial-card]:visible').evaluateAll(cards => cards.map(c => c.dataset.name))).sort();
    assert.deepEqual(actual,expected,JSON.stringify(item));
    assert.equal((await statusRegion.innerText()).trim(),`${expected.length} ${expected.length===1?'editorial':'editoriales'}`);
    const empty = page.locator('[data-editoriales-empty]');
    assert.equal(await empty.isVisible(),expected.length===0);
    const hidden = await page.locator('[data-editorial-card][hidden]').count();
    assert.equal(hidden,records.length-expected.length);
  }
  console.log('PASS editoriales filter accessible oracle');
} finally {
  await browser.close();
}
