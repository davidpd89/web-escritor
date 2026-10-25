import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try {
  for (const route of ['/libros/','/libros/samuel-entre-mundos/']) {
    for (const width of [320,390,768,1440]) {
      const page = await browser.newPage({viewport:{width,height:700}});
      try {
        const response = await page.goto(BASE+route,{waitUntil:'domcontentloaded'});
        assert.equal(response?.status(),200,`${route} ${width}: HTTP`);
        await page.locator('[data-explore-open]').click();
        const dialog = page.locator('[data-explore-dialog]');
        await assert.doesNotReject(()=>dialog.waitFor({state:'visible'}),`${route} ${width}: diálogo`);
        const selectors = ['#nl-email-explore','#newsletter-form-explore button[type=submit]','#newsletter-form-explore .form-help a'];
        for (const selector of selectors) {
          const control = dialog.locator(selector);
          await control.scrollIntoViewIfNeeded();
          const box = await control.boundingBox();
          assert.ok(box && box.width>0 && box.height>0,`${route} ${width}: ${selector} sin caja útil`);
          assert.ok(box.x>=-1 && box.x+box.width<=width+1,`${route} ${width}: ${selector} fuera horizontalmente: ${JSON.stringify(box)}`);
          assert.ok(box.y>=-1 && box.y+box.height<=701,`${route} ${width}: ${selector} no alcanzable verticalmente: ${JSON.stringify(box)}`);
        }
        await dialog.locator('#nl-email-explore').fill('lector@example.com');
        assert.equal(await dialog.locator('#nl-email-explore').inputValue(),'lector@example.com',`${route} ${width}: campo no editable`);
      } finally { await page.close(); }
    }
  }
} finally { await browser.close(); }
