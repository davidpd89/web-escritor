import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const BASE=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true});
try {
  for(const javascript of [true,false]) {
    const ctx=await browser.newContext({javaScriptEnabled:javascript});
    const sets=[];
    for(const route of ['/fragmento/','/libros/samuel-entre-mundos/']) {
      const page=await ctx.newPage();
      await page.route('**/*',r=>r.request().url().startsWith(BASE)?r.continue():r.abort());
      await page.goto(BASE+route);
      const links=await page.locator('.section-context__links a').evaluateAll(els=>els.map(a=>({href:a.getAttribute('href'),current:a.getAttribute('aria-current')})));
      const paths=links.map(x=>x.href);
      assert.equal(new Set(paths).size,paths.length,`${route}: enlaces duplicados`);
      assert.equal(links.filter(x=>x.current==='page').length,1,`${route}: aria-current ambiguo`);
      assert.equal(links.find(x=>x.current==='page').href,route);
      sets.push(paths.sort());
      await page.close();
    }
    assert.deepEqual(sets[0],sets[1],`Los destinos de Samuel divergen con JS=${javascript}`);
    await ctx.close();
  }
} finally {await browser.close();}
console.log('fragmento-context-nav-set-equality: OK');