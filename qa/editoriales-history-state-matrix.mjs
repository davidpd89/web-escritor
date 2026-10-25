import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({headless:true});
const page = await browser.newPage();

async function snapshot() {
  return page.evaluate(() => ({
    hash: location.hash,
    genre: document.querySelector('[data-editoriales-genre]').value,
    status: document.querySelector('[data-editoriales-status]').value,
    direct: document.querySelector('[data-editoriales-direct]').checked,
    visible: [...document.querySelectorAll('[data-editorial-card]')].filter(e=>!e.hidden).map(e=>e.dataset.name),
    count: document.querySelector('[data-editoriales-count]').textContent.trim()
  }));
}

try {
  await page.goto(BASE+'/editoriales/',{waitUntil:'domcontentloaded'});
  const initial = await snapshot();
  assert.ok(initial.visible.length>0);
  await page.locator('[data-editoriales-status]').selectOption('open');
  const open = await snapshot();
  assert.equal(open.status,'open');
  assert.match(open.hash,/estado=open/);
  assert.ok(open.visible.length>0);
  await page.locator('[data-editoriales-direct]').check();
  const direct = await snapshot();
  assert.equal(direct.direct,true);
  assert.match(direct.hash,/directo=1/);
  assert.ok(direct.visible.length<=open.visible.length);
  await page.goBack({waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>!document.querySelector('[data-editoriales-direct]').checked);
  assert.deepEqual(await snapshot(),open,'Atrás debe restaurar filtros y tarjetas');
  await page.goForward({waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>document.querySelector('[data-editoriales-direct]').checked);
  assert.deepEqual(await snapshot(),direct,'Adelante debe restaurar el estado completo');
  await page.locator('[data-editoriales-reset]').click();
  const reset = await snapshot();
  assert.equal(reset.hash,'');
  assert.deepEqual(reset.visible,initial.visible);
  assert.equal(reset.count,initial.count);
  console.log('PASS editoriales history state matrix');
} finally { await browser.close(); }
