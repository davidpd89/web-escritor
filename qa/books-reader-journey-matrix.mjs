import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({headless:true});
try {
  for (const javaScriptEnabled of [true,false]) {
    for (const width of [390,1280]) {
      const context = await browser.newContext({javaScriptEnabled,viewport:{width,height:900}});
      await context.route('**/*',r => new URL(r.request().url()).origin === ORIGIN ? r.continue() : r.abort());
      const page = await context.newPage();
      await page.goto(`${ORIGIN}/libros/`,{waitUntil:'domcontentloaded'});
      await page.locator('#obra-publicada .primary-action').click();
      assert.equal(new URL(page.url()).pathname,'/libros/samuel-entre-mundos/');
      assert.match(await page.locator('main h1').innerText(),/Samuel entre mundos/);
      await page.locator('.samuel-actions .primary-action').first().click();
      assert.equal(new URL(page.url()).pathname,'/fragmento/');
      assert.ok((await page.locator('main').innerText()).length>1000);
      await page.goBack({waitUntil:'domcontentloaded'});
      assert.equal(new URL(page.url()).pathname,'/libros/samuel-entre-mundos/');
      await page.goBack({waitUntil:'domcontentloaded'});
      assert.equal(new URL(page.url()).pathname,'/libros/');
      assert.match(await page.locator('#obra-publicada h2').innerText(),/Samuel entre mundos/);
      await context.close();
    }
  }
} finally { await browser.close(); }
console.log('PASS reader journeys with JS on/off and two viewports');
