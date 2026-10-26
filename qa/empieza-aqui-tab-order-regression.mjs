import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const route = '/empieza-aqui/';
const browser = await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});
try {
  for (const width of [390,1024]) {
    const context = await browser.newContext({viewport:{width,height:900}});
    const page = await context.newPage();
    await page.goto(`${ORIGIN}${route}`,{waitUntil:'load'});
    const expected = await page.locator('main .findability-entry a[href]').evaluateAll(nodes=>nodes.filter(n=>getComputedStyle(n).visibility!=='hidden' && n.getClientRects().length).map(n=>n.href));
    assert(expected.length>=7,`${route}@${width}: recorrido editorial insuficiente: ${expected.length} enlaces`);
    await page.locator('main .findability-entry a[href]').first().focus();
    const actual = [];
    for(let i=0;i<expected.length;i++) {
      const state = await page.evaluate(()=>({href:document.activeElement?.href,inside:!!document.activeElement?.closest('main .findability-entry')}));
      assert(state.inside,`${route}@${width}: el foco abandonó las rutas en posición ${i}`);
      actual.push(state.href);
      if(i<expected.length-1) await page.keyboard.press('Tab');
    }
    assert.deepEqual(actual,expected,`${route}@${width}: orden de Tab distinto del orden editorial`);
    await context.close();
  }
  console.log('empieza-aqui-tab-order-regression: OK');
} finally { await browser.close(); }
