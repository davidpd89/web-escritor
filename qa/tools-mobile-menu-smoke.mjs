import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const paths = ['/herramientas/','/herramientas/contador-palabras/','/herramientas/manuscrito/','/herramientas/dialogo/'];
const browser = await chromium.launch({headless:true});
try {
  for (const width of [320,360,390]) {
    for (const path of paths) {
      const context = await browser.newContext({viewport:{width,height:760},isMobile:true,hasTouch:true});
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror',e=>errors.push(e.message));
      try {
        const response = await page.goto(ORIGIN+path,{waitUntil:'load'});
        assert(response?.ok(),`${path} @${width}: HTTP ${response?.status()}`);
        const trigger = page.locator('[data-explore-open]');
        await trigger.waitFor({state:'visible'});
        await trigger.click();
        await page.waitForFunction(()=>document.querySelector('[data-explore-open]')?.getAttribute('aria-expanded')==='true');
        const dialog = page.locator('#explore-dialog');
        assert(await dialog.isVisible(),`${path} @${width}: menú abierto sin diálogo visible`);
        const links = dialog.locator('a[href]');
        assert(await links.count()>0,`${path} @${width}: menú sin enlaces`);
        await page.keyboard.press('Escape');
        await page.waitForFunction(()=>document.querySelector('[data-explore-open]')?.getAttribute('aria-expanded')==='false');
        assert(!(await dialog.isVisible()),`${path} @${width}: menú no se cierra con Escape`);
        assert(await page.locator('h1').first().isVisible(),`${path} @${width}: contenido inaccesible tras cerrar menú`);
        assert.deepEqual(errors,[],`${path} @${width}: errores JS ${errors.join('; ')}`);
      } finally {
        await context.close();
      }
    }
  }
} finally {
  await browser.close();
}
console.log('tools-mobile-menu-smoke: PASS');