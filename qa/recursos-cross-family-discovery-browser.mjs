import assert from 'node:assert/strict';
import { browserCase, DIRECTORY, OBJECT } from './recursos-risk-harness.mjs';

await browserCase('/herramientas/', async page => {
  for (const destination of [DIRECTORY, OBJECT]) {
    const links = page.locator(`main a[href="${destination}"]`);
    assert.ok(await links.count() >= 1, `Destino no descubrible: ${destination}`);
    const visible = links.filter({ visible: true });
    assert.ok(await visible.count() >= 1, `Enlaces ocultos hacia ${destination}`);
    const link = visible.first();
    assert.ok((await link.innerText()).trim().length > 2);
    await link.click();
    assert.equal(new URL(page.url()).pathname, destination);
    assert.equal(await page.locator('main h1').count(), 1);
    await page.goto('http://127.0.0.1:4173/herramientas/', { waitUntil: 'load' });
  }
  console.log('PASS recursos: descubrimiento desde Herramientas');
});
