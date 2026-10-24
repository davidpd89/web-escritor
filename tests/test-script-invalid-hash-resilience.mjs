import assert from 'node:assert/strict';
import { startSite, launch } from '../qa/errores-progresivo-browser-fixture.mjs';
const html = '<!doctype html><html><body><span data-samuel-quiz hidden></span><main id="contenido"><h1>Lectura de prueba</h1><input aria-label="Buscar" id="focus"><p style="height:2400px">Contenido</p><h2 id="destino">Destino</h2></main><script src="/script.js"></script></body></html>';
const site = await startSite({ '/__qa/hash.html': html });
const browser = await launch();
try {
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(site.origin + '/__qa/hash.html#%E0%A4%A', { waitUntil: 'load' });
  await page.locator('#focus').focus();
  await page.keyboard.press('a');
  await page.waitForTimeout(600);
  assert.deepEqual(errors, [], `Malformed hash raised an uncaught error: ${errors.join('; ')}`);
  assert.equal(await page.evaluate(() => document.activeElement.id), 'focus',
    'Delayed fragment correction stole input focus');
  assert(await page.locator('h1').isVisible());
} finally { await browser.close(); await site.close(); }
console.log('PASS malformed fragment and focus resilience');
