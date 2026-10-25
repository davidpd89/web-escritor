import assert from 'node:assert/strict';
import {withSite,visit} from './menu-navigation-local-fixture.mjs';

await withSite(async ({browser,origin}) => {
  for (const route of ['/eventos.html','/convocatorias-escritores/','/recomendaciones/','/editoriales/']) {
    const {page,context} = await visit(browser,origin,route,{width:390,blockShell:true});
    try {
      const footer = page.locator('footer.site-footer a[href^="/"]');
      assert(await footer.count() >= 3,`${route}: missing static navigation after script failure`);
      const opener = page.locator('[data-explore-open]').first();
      if (await opener.isVisible()) {
        await opener.click();
        const state = await page.evaluate(() => {
          const button = document.querySelector('[data-explore-open]');
          const dialog = document.querySelector('[data-explore-dialog]');
          return {opened:Boolean(dialog?.open),disabled:Boolean(button?.disabled),hidden:button?.getAttribute('aria-hidden') === 'true'};
        });
        assert(state.opened || state.disabled || state.hidden,`${route}: dead Explore button remains advertised as functional`);
      }
      const home = page.locator('a.header-home').first();
      assert(await home.count(),`${route}: missing direct Home link`);
      await home.click();
      assert.equal(new URL(page.url()).pathname,'/',`${route}: direct navigation broken`);
    } finally {await context.close();}
  }
});
console.log('OK: shell JavaScript failure recovery');
