import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({headless:true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});
try {
  const page = await browser.newPage();
  const response = await page.goto(`${BASE}/editoriales/`, {waitUntil:'domcontentloaded'});
  assert.ok(response?.ok(), '/editoriales/: respuesta HTTP incorrecta');
  const sort = page.locator('[data-editoriales-sort]');
  await sort.focus();
  for (const mode of ['name','recent','availability']) {
    await sort.selectOption(mode);
    assert.equal(await sort.evaluate(el=>document.activeElement===el),true,`/editoriales/: foco perdido al ordenar por ${mode}`);
    const count = await page.locator('[data-editorial-card]:visible').count();
    assert.ok(count>0,`/editoriales/: no quedan fichas visibles con orden ${mode}`);
    const names = await page.locator('[data-editorial-card]:visible h2').allTextContents();
    assert.equal(new Set(names).size,names.length,`/editoriales/: fichas duplicadas tras ordenar por ${mode}`);
  }
  await page.keyboard.press('Tab');
  const next = await page.evaluate(()=>({tag:document.activeElement?.tagName,visible:!!document.activeElement?.getClientRects().length}));
  assert.ok(next.visible && ['BUTTON','INPUT','SELECT','A'].includes(next.tag),`/editoriales/: Tab tras ordenar termina en ${JSON.stringify(next)}`);
} finally { await browser.close(); }
