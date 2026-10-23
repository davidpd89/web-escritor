import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const O = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const routes = ['/libros/','/cuaderno/','/recomendaciones/','/editoriales/','/convocatorias-escritores/','/herramientas/','/asistente/','/mapa-del-sitio/','/eventos.html','/ferias.html','/privacidad.html'];
const browser = await chromium.launch({headless:true});
try {
  for (const width of [320,390,1280]) {
    const context = await browser.newContext({javaScriptEnabled:false,viewport:{width,height:900}});
    await context.route('**/*', r=>r.request().url().startsWith(O+'/')?r.continue():r.abort());
    const page = await context.newPage();
    for (const route of routes) {
      await page.goto(O+route,{waitUntil:'domcontentloaded'});
      const skip = page.locator('a.skip-link[href^="#"]');
      assert.equal(await skip.count(),1,route+': skip link');
      await skip.focus();
      assert.ok(await skip.isVisible(),route+': skip link no visible al enfocarse');
      const target = await skip.getAttribute('href');
      assert.equal(await page.locator(target).count(),1,route+': destino inexistente');
      await skip.press('Enter');
      assert.equal(new URL(page.url()).hash,target,route+': hash incorrecto');
      assert.ok(await page.evaluate(id=>document.activeElement===document.getElementById(id),target.slice(1)),route+': foco no trasladado');
    }
    await context.close();
  }
} finally { await browser.close(); }
console.log('PASS nojs keyboard skip links');