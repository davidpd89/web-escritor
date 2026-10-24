import assert from 'node:assert/strict';
import { browserCase, OBJECT } from './recursos-risk-harness.mjs';

await browserCase(OBJECT, async page => {
  await page.locator('[data-object-field="title"]').fill('Reloj sin modificar');
  await page.locator('[data-rows="photos"] [data-key="filename"]').fill('prueba.jpg');
  const url = page.url();
  const downloads = [];
  page.on('download', download => downloads.push(download.suggestedFilename()));

  await page.evaluate(() => {
    window.__qaPrints = 0;
    window.__qaEvents = [];
    window.print = () => { window.__qaPrints += 1; };
    window.addEventListener('dp:analytics', event => window.__qaEvents.push(event.detail?.event));
  });

  await page.locator('[data-record-print]').click();
  const result = await page.evaluate(() => ({
    calls: window.__qaPrints,
    events: window.__qaEvents,
  }));
  assert.equal(result.calls, 1);
  assert.deepEqual(result.events, ['object_record_print']);
  assert.equal(await page.locator('[data-object-field="title"]').inputValue(), 'Reloj sin modificar');
  assert.equal(await page.locator('[data-rows="photos"] [data-key="filename"]').inputValue(), 'prueba.jpg');
  assert.deepEqual(downloads, []);
  assert.equal(page.url(), url);
  console.log('PASS recursos: intención de impresión sin efectos secundarios');
});
