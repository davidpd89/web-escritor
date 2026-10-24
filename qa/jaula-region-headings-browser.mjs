import assert from 'node:assert/strict';
import { withJaula } from './jaula-local-fixture.mjs';

await withJaula(async ({ page }) => {
  const regions = await page.evaluate(() => [...document.querySelectorAll('article.book-page section[aria-labelledby], article.book-page aside[aria-labelledby]')].map(region => {
    const id = region.getAttribute('aria-labelledby');
    const matches = [...document.querySelectorAll('[id]')].filter(el => el.id === id);
    const heading = matches[0];
    return { id, count: matches.length, inside: heading ? region.contains(heading) : false, tag: heading?.tagName, name: heading?.textContent.trim(), visible: heading ? getComputedStyle(heading).display !== 'none' && getComputedStyle(heading).visibility !== 'hidden' : false };
  }));
  assert.equal(regions.length, 2, 'Deben existir el capítulo y el bloque de continuidad');
  for (const region of regions) {
    assert.equal(region.count, 1, `ID ambiguo: ${region.id}`);
    assert.equal(region.inside, true, `Encabezado fuera de su región: ${region.id}`);
    assert.match(region.tag || '', /^H[2-6]$/);
    assert.ok(region.name?.length > 0 && region.visible, `Encabezado inaccesible: ${region.id}`);
  }
  assert.equal(await page.locator('article.book-page h1').count(), 1);
});
console.log('jaula-region-headings-browser: OK');
