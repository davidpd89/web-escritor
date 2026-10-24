import assert from 'node:assert/strict';
import { withJaula } from './jaula-local-fixture.mjs';

await withJaula(async ({ page }) => {
  for (const [selector, target] of [['.book-actions .text-action', '/libros/'], ['.book-related .related-primary a', '/libros/'], ['.related-secondary a[href="/autor.html"]', '/autor.html'], ['.related-secondary a[href="/cuaderno/"]', '/cuaderno/']]) {
    const link = page.locator(selector);
    assert.equal(await link.getAttribute('href'), target);
    await link.click();
    await page.waitForURL(url => url.pathname === target);
    assert.equal(await page.locator('main').count(), 1, `Destino sin main: ${target}`);
    assert.ok((await page.locator('main').innerText()).trim().length > 50, `Destino vacío: ${target}`);
    await page.goBack({ waitUntil: 'domcontentloaded' });
    assert.equal(new URL(page.url()).pathname, '/donde-empieza-la-jaula/');
    assert.equal(await page.locator('#capitulo-1 .excerpt-field p').count(), 133);
  }
});
console.log('jaula-continuation-journeys: OK');
