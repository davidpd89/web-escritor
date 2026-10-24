import assert from 'node:assert/strict';
import { withJaula } from './jaula-local-fixture.mjs';

await withJaula(async ({ page }) => {
  assert.equal(await page.locator('#capitulo-1 .excerpt-field p').count(), 133);
  assert.equal(await page.locator('h1').textContent(), 'Dónde empieza la jaula');
  await page.locator('.book-actions .primary-action').click();
  assert.equal(new URL(page.url()).hash, '#capitulo-1');
  assert.equal(await page.locator('#jaula-capitulo-1').isVisible(), true);
  const href = await page.locator('.book-actions .text-action').getAttribute('href');
  assert.equal(href, '/libros/');
  await page.locator('.book-actions .text-action').click();
  await page.waitForURL('**/libros/');
  assert.equal(await page.locator('main').count(), 1);
}, { failPaths: ['/assets/v1-shell.js'] });
console.log('jaula-shell-failure-browser: OK');
