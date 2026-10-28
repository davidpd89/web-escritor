import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const routes = ['/asistente/', '/herramientas/', '/recomendaciones/'];
const destinations = ['/libros/', '/recomendaciones/', '/herramientas/'];
const browser = await chromium.launch({headless:true});
try {
  const context = await browser.newContext({javaScriptEnabled:false, viewport:{width:390,height:844},serviceWorkers:'block'});
  const page = await context.newPage();
  for (const route of routes) {
    const response = await page.goto(ORIGIN + route, {waitUntil:'load'});
    assert.ok(response?.ok(), `${route}: HTTP ${response?.status()}`);
    assert.ok(await page.locator('h1').count(), `${route}: falta H1 sin JavaScript`);
    for (const destination of destinations) {
      const links = page.locator(`a[href='${destination}']`);
      let visible = false;
      for (let i=0;i<await links.count();i++) {
        if (await links.nth(i).isVisible()) { visible=true; break; }
      }
      assert.ok(visible, `${route}: no existe navegación visible hacia ${destination} sin JavaScript`);
    }
  }
  await context.close();
} finally {
  await browser.close();
}
console.log('nojs-primary-navigation-smoke: PASS');