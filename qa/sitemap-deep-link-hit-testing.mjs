import assert from 'node:assert/strict';
import {withSitemapBrowser} from './sitemap-offline-browser-helper.mjs';

await withSitemapBrowser(async ({newPage,origin}) => {
  for (const width of [320,390]) {
    const {page,context} = await newPage({viewport:{width,height:844},hasTouch:true});
    try {
      for (let i=0;i<4;i++) {
        const panel = page.locator('main details').nth(i);
        if (!await panel.evaluate(el=>el.open)) await panel.locator('summary').click();
        const links = panel.locator('a[href]');
        const count = await links.count();
        assert(count>=3);
        const positions = [...new Set([0,Math.floor(count/2),count-1])];
        for (const index of positions) {
          const link = links.nth(index);
          await link.scrollIntoViewIfNeeded();
          const rect = await link.boundingBox();
          assert(rect && rect.width>0 && rect.height>=40,`${i}/${index}: superficie insuficiente`);
          const x = rect.x + rect.width/2;
          const y = rect.y + rect.height/2;
          assert(x>=0 && x<width && y>=0 && y<844,`${i}/${index}: fuera de viewport`);
          const hittable = await link.evaluate((el,p) => { const hit=document.elementFromPoint(p.x,p.y); return Boolean(hit && (hit===el || el.contains(hit))); },{x,y});
          assert(hittable,`${i}/${index}: otro elemento intercepta el centro`);
        }
        const last = links.last();
        const target = new URL(await last.getAttribute('href'),origin).pathname;
        await last.click();
        assert.equal(new URL(page.url()).pathname,target,`${i}: el último enlace no navega correctamente`);
        await page.goBack({waitUntil:'load'});
        assert.equal(new URL(page.url()).pathname,'/mapa-del-sitio/');
      }
    } finally { await context.close(); }
  }
});
console.log('PASS sitemap deep link hit testing');
