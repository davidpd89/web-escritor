import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({headless:true});
try {
  for(const width of [320,390,1024]) {
    const context = await browser.newContext({viewport:{width,height:800},javaScriptEnabled:false});
    const page = await context.newPage();
    try {
      const response = await page.goto(`${BASE}/metodologia-editorial/`,{waitUntil:'domcontentloaded'});
      assert.equal(response?.status(),200);
      const contact = page.locator('main .tool-findings-block a[data-email-reveal]');
      assert.equal(await contact.getAttribute('href'),'/prensa.html#contacto');
      await contact.focus();
      await page.keyboard.press('Enter');
      await page.waitForURL('**/prensa.html#contacto');
      const target = page.locator('#contacto');
      assert.equal(await target.count(),1);
      assert.equal(await target.isVisible(),true);
      assert.ok((await target.innerText()).trim().length>25);
    } finally { await context.close(); }
  }
  console.log('PASS no-JS methodology correction journey');
} finally { await browser.close(); }