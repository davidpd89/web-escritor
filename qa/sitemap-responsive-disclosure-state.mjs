import assert from 'node:assert/strict';
import {withSitemapBrowser} from './sitemap-offline-browser-helper.mjs';

await withSitemapBrowser(async ({newPage}) => {
  const {page,context} = await newPage({viewport:{width:390,height:844}});
  try {
    const panels = page.locator('main details');
    assert.equal(await panels.count(),4);
    for (const i of [0,2]) await panels.nth(i).locator('summary').click();
    for (const size of [{width:320,height:900},{width:620,height:900},{width:900,height:650},{width:1440,height:900},{width:844,height:390},{width:390,height:844}]) {
      await page.setViewportSize(size);
      await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
      const states = await panels.evaluateAll(ns=>ns.map(n=>n.open));
      assert.deepEqual(states,[true,false,true,false],`estado alterado en ${size.width}x${size.height}`);
      for (let i=0;i<4;i++) assert.equal(await panels.nth(i).locator('a').first().isVisible(),states[i]);
      const metrics = await page.evaluate(()=>({scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth}));
      assert(metrics.scroll<=metrics.client+1,`overflow ${JSON.stringify(size)}: ${JSON.stringify(metrics)}`);
    }
    await panels.nth(0).locator('summary').click();
    assert.deepEqual(await panels.evaluateAll(ns=>ns.map(n=>n.open)),[false,false,true,false]);
  } finally { await context.close(); }
});
console.log('PASS sitemap responsive state');
