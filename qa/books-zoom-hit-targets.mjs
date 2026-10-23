import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({headless:true});
try {
  for (const width of [320,390]) {
    const context = await browser.newContext({viewport:{width,height:568},reducedMotion:'reduce'});
    await context.route('**/*',r => new URL(r.request().url()).origin === ORIGIN ? r.continue() : r.abort());
    const page = await context.newPage();
    await page.goto(`${ORIGIN}/libros/samuel-entre-mundos/`,{waitUntil:'load'});
    await page.addStyleTag({content:'html{font-size:200%!important}body{letter-spacing:.12em!important;word-spacing:.16em!important;line-height:1.5!important}'});
    for (const selector of ['.samuel-actions .primary-action','.samuel-actions [data-buy-modal]','.quiz-option']) {
      const target = page.locator(selector).first();
      await target.scrollIntoViewIfNeeded();
      const bounds = await target.boundingBox();
      assert.ok(bounds && bounds.width>=24 && bounds.height>=24,`${width}: ${selector} área insuficiente`);
      const hit = await target.evaluate(el => {
        const r=el.getBoundingClientRect();
        const found=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);
        return found === el || el.contains(found);
      });
      assert.equal(hit,true,`${width}: ${selector} tapado`);
    }
    await page.locator('.samuel-actions [data-buy-modal]').first().click();
    const close = page.locator('#buy-dialog-close');
    await close.scrollIntoViewIfNeeded();
    assert.equal(await close.isVisible(),true);
    const box=await close.boundingBox();
    assert.ok(box && box.width>=24 && box.height>=24);
    await context.close();
  }
} finally { await browser.close(); }
console.log('PASS hit targets at 200% text zoom');
