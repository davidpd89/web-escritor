import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const ORIGIN = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const ROUTES = ['/', '/libros/', '/recomendaciones/', '/herramientas/', '/editoriales/', '/cuaderno/', '/asistente/', '/mapa-del-sitio/', '/eventos.html', '/ferias.html', '/premios.html', '/privacidad.html'];
const EXPECTED = ['/libros/', '/recomendaciones/', '/herramientas/'];
const browser = await chromium.launch({headless:true});
try {
  const context = await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844}});
  await context.route('**/*', r => r.request().url().startsWith(ORIGIN + '/') ? r.continue() : r.abort());
  const page = await context.newPage();
  for (const route of ROUTES) {
    const response = await page.goto(ORIGIN + route, {waitUntil:'domcontentloaded'});
    assert.equal(response?.status(), 200, route);
    const links = await page.locator('header .primary-nav a:visible').evaluateAll(nodes => nodes.map(a => ({href:a.getAttribute('href'),name:a.textContent.trim()})));
    for (const target of EXPECTED) assert.ok(links.some(a=>a.href===target && a.name), route + ': destino ausente ' + target);
    await page.locator('header .primary-nav a[href="/libros/"]').click();
    assert.equal(new URL(page.url()).pathname, '/libros/', route + ': enlace no navegable');
  }
  await context.close();
} finally { await browser.close(); }
console.log('PASS nojs global navigation parity');