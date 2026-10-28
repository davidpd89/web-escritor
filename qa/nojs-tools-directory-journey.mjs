import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const destinations = ['/herramientas/manuscrito/', '/herramientas/dialogo/', '/herramientas/contador-palabras/'];
const browser = await chromium.launch({headless:true});
try {
  const context = await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844},serviceWorkers:'block'});
  const page = await context.newPage();
  const response = await page.goto(ORIGIN+'/herramientas/',{waitUntil:'load'});
  assert.ok(response?.ok(), `/herramientas/: HTTP ${response?.status()}`);
  for (const destination of destinations) {
    const links = page.locator(`a[href='${destination}']`);
    let link = null;
    for (let i=0;i<await links.count();i++) {
      if (await links.nth(i).isVisible()) {link=links.nth(i);break;}
    }
    assert.ok(link, `/herramientas/: falta enlace visible hacia ${destination}`);
    await link.click();
    await page.waitForURL(url=>url.pathname===destination);
    assert.ok(await page.locator('h1').count(), `${destination}: falta encabezado principal`);
    assert.ok((await page.locator('body').innerText()).trim().length>100, `${destination}: documento sin contenido útil`);
    await page.goto(ORIGIN+'/herramientas/',{waitUntil:'load'});
  }
  await context.close();
} finally {
  await browser.close();
}
console.log('nojs-tools-directory-journey: PASS');