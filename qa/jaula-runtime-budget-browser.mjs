import assert from 'node:assert/strict';
import { withJaula } from './jaula-local-fixture.mjs';

await withJaula(async ({ page, served, missing }) => {
  await page.locator('.excerpt-field p').last().scrollIntoViewIfNeeded();
  const metrics = await page.evaluate(() => ({ elements: document.querySelectorAll('*').length, paragraphs: document.querySelectorAll('.excerpt-field p').length, stylesheets: document.styleSheets.length, scripts: document.scripts.length, overflow: document.documentElement.scrollWidth - innerWidth }));
  const broken = missing.filter(item => ['script', 'stylesheet'].includes(item.type));
  assert.deepEqual(broken, [], `Dependencias locales ausentes: ${JSON.stringify(broken)}`);
  assert.equal(metrics.paragraphs, 133);
  assert.ok(metrics.elements < 1800, `DOM excesivo: ${metrics.elements}`);
  assert.ok(metrics.stylesheets < 100, `Demasiadas hojas de estilo: ${metrics.stylesheets}`);
  assert.ok(metrics.overflow <= 1);
  const totalBytes = served.reduce((sum, resource) => sum + resource.bytes, 0);
  assert.ok(totalBytes < 6 * 1024 * 1024, `Recursos locales por encima de 6 MiB: ${totalBytes}`);
});
console.log('jaula-runtime-budget-browser: OK');
