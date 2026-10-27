import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN=(process.env.QA_ORIGIN||'http://127.0.0.1:4173').replace(/\/$/,'');
const routes=['/cuaderno/que-es-el-portal-fantasy/','/recomendaciones/portal-fantasy-espanol/'];
const browser=await chromium.launch({headless:true});
try {
  const context=await browser.newContext({serviceWorkers:'block'});
  await context.route('**/assets/newsletter-popup.js*',route=>route.abort('failed'));
  const page=await context.newPage();
  for(const route of routes) {
    const errors=[];
    const handler=error=>errors.push(error.message);
    page.on('pageerror',handler);
    const response=await page.goto(ORIGIN+route,{waitUntil:'load'});
    assert.ok(response?.ok(),`${route}: HTTP ${response?.status()}`);
    assert.ok(await page.locator('h1').first().isVisible(),`${route}: encabezado no visible`);
    const content=await page.locator('main').innerText();
    assert.ok(content.trim().length>200,`${route}: contenido editorial ausente al fallar newsletter-popup.js`);
    const links=page.locator('main a[href]');
    assert.ok(await links.count()>0,`${route}: faltan enlaces editoriales`);
    assert.deepEqual(errors,[],`${route}: errores JavaScript: ${errors.join('; ')}`);
    page.off('pageerror',handler);
  }
  await context.close();
} finally {
  await browser.close();
}
console.log('newsletter-script-failure-content-smoke: PASS');