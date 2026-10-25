import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch({headless:true});
const page = await browser.newPage();

async function snapshot() {
  return page.evaluate(() => ({
    hash: location.hash,
    genre: document.querySelector('[data-editoriales-genre]').value,
    status: document.querySelector('[data-editoriales-status]').value,
    country: document.querySelector('[data-editoriales-country]').value,
    sort: document.querySelector('[data-editoriales-sort]').value,
    direct: document.querySelector('[data-editoriales-direct]').checked,
    count: document.querySelector('[data-editoriales-count]').textContent.trim(),
    visible: [...document.querySelectorAll('[data-editorial-card]')].filter(c => !c.hidden).map(c => c.dataset.name)
  }));
}

async function expectRestored(expected) {
  await page.waitForFunction(e => {
    const root = document.querySelector('[data-editoriales-directory]');
    return root && location.hash === e.hash &&
      root.querySelector('[data-editoriales-genre]').value === e.genre &&
      root.querySelector('[data-editoriales-status]').value === e.status &&
      root.querySelector('[data-editoriales-country]').value === e.country &&
      root.querySelector('[data-editoriales-sort]').value === e.sort &&
      root.querySelector('[data-editoriales-direct]').checked === e.direct;
  }, expected);
  assert.deepEqual(await snapshot(), expected);
}

try {
  const response = await page.goto(BASE + '/editoriales/', {waitUntil:'domcontentloaded'});
  assert.ok(response?.ok());
  const initial = await snapshot();
  assert.ok(initial.visible.length > 0);

  await page.locator('[data-editoriales-genre]').selectOption('fantasía');
  const fantasy = await snapshot();
  assert.equal(fantasy.genre, 'fantasía');
  assert.ok(fantasy.visible.length > 0);

  await page.locator('[data-editoriales-status]').selectOption('open');
  const opened = await snapshot();
  assert.equal(opened.status, 'open');

  await page.locator('[data-editoriales-sort]').selectOption('name');
  const sorted = await snapshot();
  assert.equal(sorted.sort, 'name');

  await page.goBack({waitUntil:'domcontentloaded'});
  await expectRestored(opened);
  await page.goBack({waitUntil:'domcontentloaded'});
  await expectRestored(fantasy);
  await page.goBack({waitUntil:'domcontentloaded'});
  await expectRestored(initial);
  await page.goForward({waitUntil:'domcontentloaded'});
  await expectRestored(fantasy);
  await page.goForward({waitUntil:'domcontentloaded'});
  await expectRestored(opened);
  await page.goForward({waitUntil:'domcontentloaded'});
  await expectRestored(sorted);

  const link = page.locator('[data-editorial-card]:visible h2 a').first();
  assert.ok(await link.count(), 'La selección debe contener una ficha navegable');
  const beforeDetail = await snapshot();
  await link.click();
  assert.match(page.url(), /\/editoriales\/[^/]+\/$/);
  await page.goBack({waitUntil:'domcontentloaded'});
  await expectRestored(beforeDetail);
  console.log('PASS editoriales history intent matrix');
} finally {
  await browser.close();
}
