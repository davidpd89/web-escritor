import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const browser = await chromium.launch({headless:true});
try {
  const context = await browser.newContext({serviceWorkers:'block'});
  await context.route('**/assets/reading-catalogue.js*', route=>route.abort('failed'));
  const page = await context.newPage();
  const errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  const response = await page.goto(ORIGIN+'/recomendaciones/',{waitUntil:'load'});
  assert.ok(response?.ok(), `/recomendaciones/: HTTP ${response?.status()}`);
  assert.ok(await page.locator('h1').isVisible(), '/recomendaciones/: falta título principal');
  const links=page.locator('a[href^="/recomendaciones/libros/"]');
  let usable=null;
  for(let i=0;i<await links.count();i++) {
    const link=links.nth(i);
    if(await link.isVisible() && (await link.innerText()).trim().length>2) {usable=link;break;}
  }
  assert.ok(usable, '/recomendaciones/: no quedan enlaces bibliográficos textuales visibles al fallar el script');
  const href=await usable.getAttribute('href');
  const detail=await page.request.get(ORIGIN+href);
  assert.ok(detail.ok(), `/recomendaciones/: ficha ${href} devuelve HTTP ${detail.status()}`);
  assert.deepEqual(errors,[], `/recomendaciones/: errores JS adicionales: ${errors.join('; ')}`);
  await context.close();
} finally {
  await browser.close();
}
console.log('reading-catalogue-script-failure-smoke: PASS');