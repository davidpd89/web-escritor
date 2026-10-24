import assert from 'node:assert/strict';
import {withSitemapBrowser} from './sitemap-offline-browser-helper.mjs';

await withSitemapBrowser(async ({newPage}) => {
  const {page,context}=await newPage({javaScriptEnabled:false,viewport:{width:1280,height:900}});
  try {
    const panels=page.locator('main details');
    assert.equal(await panels.count(),4);
    assert.deepEqual(await panels.evaluateAll(ns=>ns.map(n=>n.open)),[false,false,false,false]);
    await page.emulateMedia({media:'print'});
    const report=await page.evaluate(() => [...document.querySelectorAll('main details')].map(panel=>{
      const links=[...panel.querySelectorAll('a[href]')];
      const visible=links.filter(a=>{
        const s=getComputedStyle(a),r=a.getBoundingClientRect();
        return s.display!=='none' && s.visibility!=='hidden' && r.width>0 && r.height>0;
      });
      return {summary:panel.querySelector('summary')?.textContent.trim(),total:links.length,visible:visible.length};
    }));
    for(const entry of report) {
      assert(entry.total>0);
      assert.equal(entry.visible,entry.total,`print oculta enlaces de ${entry.summary}: ${JSON.stringify(entry)}`);
    }
  } finally { await context.close(); }
});
console.log('PASS sitemap print catalogue preservation');
