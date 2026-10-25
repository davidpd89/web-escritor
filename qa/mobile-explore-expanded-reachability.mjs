import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN;
assert.ok(origin, 'QA_ORIGIN debe apuntar al servidor local del repositorio');
const browser = await chromium.launch({headless:true});
try {
  for (const width of [320,390]) {
    for (const height of [568,667]) {
      const page = await browser.newPage({viewport:{width,height}, reducedMotion:'reduce'});
      try {
        await page.goto(new URL('/404.html',origin).href,{waitUntil:'load'});
        await page.locator('[data-explore-open]:visible').first().click();
        const dialog = page.locator('[data-explore-dialog]');
        await dialog.waitFor({state:'visible'});
        for (const toggle of await dialog.locator('.explore-row__toggle:visible').all()) {
          if (await toggle.getAttribute('aria-expanded') === 'false') await toggle.click();
        }
        const links = dialog.locator('a:visible');
        assert.ok(await links.count()>0,`${width}x${height}: menú sin enlaces visibles`);
        const last = links.last();
        await last.scrollIntoViewIfNeeded();
        const geometry = await last.evaluate(el=>{const r=el.getBoundingClientRect();const d=el.closest('dialog').getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,dialogLeft:d.left,dialogRight:d.right,dialogTop:d.top,dialogBottom:d.bottom};});
        assert.ok(geometry.left>=geometry.dialogLeft-2 && geometry.right<=geometry.dialogRight+2 && geometry.top>=geometry.dialogTop-2 && geometry.bottom<=geometry.dialogBottom+2,`${width}x${height}: último enlace fuera del diálogo: ${JSON.stringify(geometry)}`);
        assert.ok(await last.isEnabled(),`${width}x${height}: último enlace deshabilitado`);
      } finally {await page.close();}
    }
  }
} finally {await browser.close();}