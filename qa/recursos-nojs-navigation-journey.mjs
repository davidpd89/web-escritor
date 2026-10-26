import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const ROUTE = '/recursos/ficha-historia-objeto-heredado/';
const browser = await chromium.launch({headless:true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});

try {
  const context = await browser.newContext({javaScriptEnabled:false});
  const page = await context.newPage();
  const response = await page.goto(BASE + ROUTE, {waitUntil:'domcontentloaded'});
  assert.ok(response?.ok(), `${ROUTE}: documento inaccesible`);
  const links = page.locator('a[href]');
  let selected = null;
  for (const link of await links.all()) {
    if (!(await link.isVisible())) continue;
    const href = await link.getAttribute('href');
    if (new URL(href, BASE + ROUTE).pathname === '/herramientas/') { selected = link; break; }
  }
  assert.ok(selected, `${ROUTE}: no existe enlace visible hacia /herramientas/ sin JavaScript`);
  const destination = await Promise.all([page.waitForURL(url => url.pathname === '/herramientas/'), selected.click()]);
  assert.equal(new URL(page.url()).pathname, '/herramientas/', `${ROUTE}: la navegación no alcanza el catálogo`);
  assert.ok((await page.locator('main').innerText()).trim().length > 0, '/herramientas/: destino sin contenido principal');
  console.log('OK recursos-nojs-navigation-journey');
} finally {
  await browser.close();
}
