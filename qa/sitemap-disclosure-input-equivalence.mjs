import assert from 'node:assert/strict';
import {withSitemapBrowser} from './sitemap-offline-browser-helper.mjs';

await withSitemapBrowser(async ({newPage}) => {
  for (const enabled of [false,true]) {
    for (const width of [320,390,1024]) {
      const {page,context} = await newPage({javaScriptEnabled:enabled,viewport:{width,height:900},reducedMotion:'reduce'});
      try {
        const panels = page.locator('main details');
        assert.equal(await panels.count(),4,'deben existir cuatro catálogos');
        for (let i=0;i<4;i++) {
          const panel = panels.nth(i);
          const summary = panel.locator('summary');
          const first = panel.locator('a[href]').first();
          assert.equal(await panel.evaluate(el=>el.open),false);
          assert.equal(await first.isVisible(),false);
          for (const mode of ['mouse','Enter','Space']) {
            const toggle = async () => {
              if (mode==='mouse') await summary.click();
              else { await summary.focus(); await page.keyboard.press(mode); }
            };
            await toggle();
            assert.equal(await panel.evaluate(el=>el.open),true,`${width}/${enabled}/${i}/${mode}: no abre`);
            assert(await first.isVisible(),`${width}/${enabled}/${i}/${mode}: contenido invisible`);
            await toggle();
            assert.equal(await panel.evaluate(el=>el.open),false,`${width}/${enabled}/${i}/${mode}: no cierra`);
            assert.equal(await first.isVisible(),false);
          }
        }
      } finally { await context.close(); }
    }
  }
});
console.log('PASS sitemap disclosure input equivalence');
