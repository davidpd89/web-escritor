import assert from 'node:assert/strict';
import {withSitemapBrowser} from './sitemap-offline-browser-helper.mjs';

await withSitemapBrowser(async ({newPage}) => {
  for (const width of [320,390]) {
    const {page,context} = await newPage({viewport:{width,height:900}});
    try {
      await page.route(/\.(woff2?|ttf|otf)(\?|$)/i,route=>route.abort());
      await page.reload({waitUntil:'load'});
      await page.locator('main details').evaluateAll(ns=>ns.forEach(n=>n.open=true));
      await page.evaluate(() => {
        document.documentElement.style.fontSize='200%';
        const blocks=[...document.querySelectorAll('main details')];
        for (const block of blocks) {
          const a=block.querySelector('a[href]');
          a.textContent='Título extraordinariamente extenso para comprobar la lectura, la accesibilidad y el desbordamiento: '+ 'LiteraturaFantásticaExtraordinaria'.repeat(7);
        }
      });
      await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
      const result=await page.evaluate(()=>({viewport:document.documentElement.clientWidth,document:document.documentElement.scrollWidth,links:[...document.querySelectorAll('main details a[href]')].filter(a=>a.getBoundingClientRect().width>0).slice(0,4).map(a=>({href:a.getAttribute('href'),width:a.getBoundingClientRect().width,left:a.getBoundingClientRect().left,right:a.getBoundingClientRect().right}))}));
      assert(result.document<=result.viewport+1,`${width}: desbordamiento ${JSON.stringify(result)}`);
      assert.equal(result.links.length,4);
      for (const item of result.links) assert(item.left>=-1 && item.right<=result.viewport+1,`enlace recortado: ${JSON.stringify(item)}`);
    } finally { await context.close(); }
  }
});
console.log('PASS sitemap long label mutation');
