import assert from 'node:assert/strict';
import { browserCase, DIRECTORY } from './recursos-risk-harness.mjs';

await browserCase(DIRECTORY, async page => {
  const canonical = await page.locator('link[rel="canonical"]').getAttribute('href');
  assert.equal(canonical, 'https://davidportodiaz.com' + DIRECTORY);
  assert.doesNotMatch(await page.locator('meta[name="robots"]').getAttribute('content') || '', /noindex/i);
  assert.equal(await page.locator('html').getAttribute('lang'), 'es');
  const description = await page.locator('meta[name="description"]').getAttribute('content');
  assert.ok(description && description.length >= 90);

  const structured = await page.locator('script[type="application/ld+json"]').allTextContents();
  const schemas = structured.map(JSON.parse);
  const collection = schemas.find(value => value['@type'] === 'CollectionPage');
  assert.ok(collection, 'No se identifica CollectionPage');
  assert.equal(collection.url, canonical);
  assert.equal(collection.inLanguage, 'es');
  assert.match(collection.name, /herramientas para escritores/i);
  assert.equal(await page.locator('main h1').count(), 1);

  const names = await page.locator('.wt-card h2').allInnerTexts();
  assert.equal(names.length, 8);
  assert.equal(new Set(names.map(s => s.toLocaleLowerCase('es'))).size, names.length);
  assert.equal(await page.locator('.wt-card [itemprop="aggregateRating"]').count(), 0);
  console.log('PASS recursos: semántica SEO de directorio');
});
