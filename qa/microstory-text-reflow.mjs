import assert from 'node:assert/strict';
import {withPage} from './microstory-offline-harness.mjs';

for (const width of [320,390,768,1280]) {
  await withPage(async ({page}) => {
    const original=await page.locator('.microstory-text p').innerText();
    assert.ok(original.length>400);
    for (const multiplier of [1,2,4]) {
      await page.locator('.microstory-text p').evaluate((e,m)=>{e.textContent=(e.textContent+' ').repeat(m).trim();},multiplier);
      await page.evaluate(()=>{document.documentElement.style.fontSize='125%';});
      const metrics=await page.locator('.microstory-text p').evaluate(e=>({height:e.getBoundingClientRect().height,scroll:e.scrollHeight,client:e.clientHeight,font:parseFloat(getComputedStyle(e).fontSize),line:parseFloat(getComputedStyle(e).lineHeight)}));
      assert.ok(metrics.height>0);
      assert.ok(metrics.scroll<=metrics.client+2,`${width}: clipped paragraph`);
      assert.ok(metrics.font>=16);
      assert.ok(metrics.line/metrics.font>=1.45);
      const overflow=await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth);
      assert.ok(overflow<=1,`${width}: overflow after mutation ${multiplier}`);
      await page.locator('.microstory-text p').evaluate((e,s)=>e.textContent=s,original);
    }
  },width);
}
console.log('PASS microstory text reflow');
