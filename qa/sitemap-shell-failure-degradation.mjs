import assert from 'node:assert/strict';
import {withSitemapBrowser} from './sitemap-offline-browser-helper.mjs';

await withSitemapBrowser(async ({newPage,origin}) => {
  const {page,context}=await newPage({javaScriptEnabled:true,viewport:{width:390,height:844}});
  try {
    await page.route('**/assets/v1-shell.js*',route=>route.abort());
    await page.reload({waitUntil:'load'});
    assert(await page.locator('main h1').isVisible());
    assert.equal(await page.locator('main details').count(),4);
    for (let i=0;i<4;i++) {
      const panel=page.locator('main details').nth(i);
      if (!await panel.evaluate(el=>el.open)) await panel.locator('summary').click();
      const link=panel.locator('a[href]').last();
      assert(await link.isVisible());
      const target=new URL(await link.getAttribute('href'),origin).pathname;
      await link.click();
      assert.equal(new URL(page.url()).pathname,target,`${i}: destino inaccesible sin shell`);
      await page.goBack({waitUntil:'load'});
      assert.equal(new URL(page.url()).pathname,'/mapa-del-sitio/');
    }
  } finally { await context.close(); }
});
console.log('PASS sitemap shell-failure degradation');
