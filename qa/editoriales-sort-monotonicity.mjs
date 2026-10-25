import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch();
const page = await browser.newPage();
const collator = new Intl.Collator('es',{sensitivity:'base'});

async function visible() {
  return page.locator('[data-editorial-card]:visible').evaluateAll(cards => cards.map(c => ({name:c.dataset.name,date:c.dataset.verifiedAt})));
}

try {
  const response = await page.goto(BASE+'/editoriales/',{waitUntil:'domcontentloaded'});
  assert.ok(response?.ok());
  const original = await visible();
  assert.ok(original.length >= 100);

  for(const genre of ['', 'fantasía', 'narrativa']) {
    await page.locator('[data-editoriales-genre]').selectOption(genre);
    const subset = await visible();
    for(const mode of ['name','recent','availability','name','recent']) {
      await page.locator('[data-editoriales-sort]').selectOption(mode);
      const actual = await visible();
      const expected = [...subset].sort((a,b) => {
        if(mode==='name') return collator.compare(a.name,b.name);
        if(mode==='recent') return b.date.localeCompare(a.date)||collator.compare(a.name,b.name);
        return original.findIndex(x=>x.name===a.name)-original.findIndex(x=>x.name===b.name);
      });
      assert.deepEqual(actual,expected,`Género ${genre}, orden ${mode}`);
    }
  }
  console.log('PASS editoriales sort monotonicity');
} finally {
  await browser.close();
}
