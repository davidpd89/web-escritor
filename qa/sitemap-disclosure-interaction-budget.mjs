import assert from 'node:assert/strict';
import {withSitemapBrowser} from './sitemap-offline-browser-helper.mjs';

await withSitemapBrowser(async ({newPage}) => {
  for (const width of [390,1440]) {
    const {page,context}=await newPage({viewport:{width,height:900},reducedMotion:'reduce'});
    try {
      const panels=page.locator('main details');
      assert.equal(await panels.count(),4);
      assert.equal(await page.locator('main details a:visible').count(),0);
      const durations=[];
      for (let repetition=0;repetition<3;repetition++) {
        for (let i=0;i<4;i++) {
          const panel=panels.nth(i);
          const summary=panel.locator('summary');
          for (const expected of [true,false]) {
            const start=await page.evaluate(()=>performance.now());
            await summary.click();
            await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
            const duration=await page.evaluate(()=>performance.now())-start;
            durations.push(duration);
            assert.equal(await panel.evaluate(el=>el.open),expected);
          }
        }
      }
      durations.sort((a,b)=>a-b);
      const median=(durations[11]+durations[12])/2;
      assert(median<1500,`${width}: latencia mediana ${median.toFixed(1)} ms`);
      console.log(`${width}px median ${median.toFixed(1)} ms`);
    } finally { await context.close(); }
  }
});
console.log('PASS sitemap interaction budget');
