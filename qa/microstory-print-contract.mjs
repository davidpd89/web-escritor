import assert from 'node:assert/strict';
import {withPage} from './microstory-offline-harness.mjs';

await withPage(async ({page}) => {
  await page.emulateMedia({media:'print'});
  for (const selector of ['main h1','.microstory-text p','.microstory-signature']) {
    assert.equal(await page.locator(selector).isVisible(),true,selector+' missing in print');
  }
  for (const selector of ['.site-header','.site-footer','.microstory-book','.microstory-shot','.microstory-sources','.microstory-actions','#seguir']) {
    const elements=page.locator(selector);
    for(let i=0;i<await elements.count();i++) assert.equal(await elements.nth(i).isVisible(),false,selector+' visible in print');
  }
  const style=await page.locator('.microstory-text p').evaluate(e=>({size:parseFloat(getComputedStyle(e).fontSize),line:parseFloat(getComputedStyle(e).lineHeight)}));
  assert.ok(style.size>=14);
  assert.ok(style.line/style.size>=1.35);
});
console.log('PASS microstory print contract');
