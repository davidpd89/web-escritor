import assert from 'node:assert/strict';
import { withJaula } from './jaula-local-fixture.mjs';

for (const width of [320, 390, 768, 1440]) {
  await withJaula(async ({ page }) => {
    const paragraphs = page.locator('#capitulo-1 .excerpt-field p');
    assert.equal(await paragraphs.count(), 133, `${width}: capítulo incompleto`);
    assert.equal((await paragraphs.first().textContent()).trim(), 'El orbe salía del agua y subía.');
    await page.locator('.book-actions .primary-action').click();
    assert.equal(new URL(page.url()).hash, '#capitulo-1');
    await paragraphs.last().scrollIntoViewIfNeeded();
    const last = await paragraphs.last().textContent();
    assert.ok(last.includes('volver a cerrarlo.'));
    assert.equal(await paragraphs.last().isVisible(), true);
    assert.equal(await page.locator('noscript .primary-nav a[href="/libros/"]').count(), 1);
  }, { width, javaScriptEnabled: false });
}
console.log('jaula-nojs-longform-browser: OK');
