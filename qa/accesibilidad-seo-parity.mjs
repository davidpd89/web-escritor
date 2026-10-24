import assert from 'node:assert/strict';
import { check } from './accesibilidad-fixture.mjs';

await check(async ({ page }) => {
  const data = await page.evaluate(() => {
    const meta = key => document.querySelector(`meta[property="${key}"]`)?.content;
    const canonical = [...document.querySelectorAll('link[rel="canonical"]')];
    const json = [...document.querySelectorAll('script[type="application/ld+json"]')].map(s => JSON.parse(s.textContent));
    return { title: document.title, h1: document.querySelector('main h1')?.textContent.trim(), canonical: canonical.map(x => x.href), og: meta('og:url'), ogTitle: meta('og:title'), twitter: document.querySelector('meta[name="twitter:title"]')?.content, robots: document.querySelector('meta[name="robots"]')?.content, page: json.find(x => x['@type'] === 'WebPage') };
  });
  const expected = 'https://davidportodiaz.com/accesibilidad/';
  assert.deepEqual(data.canonical, [expected]);
  assert.equal(data.og, expected);
  assert.equal(data.page.url, expected);
  assert.equal(data.page['@id'], expected + '#page');
  assert.equal(data.page.inLanguage, 'es');
  assert.ok(data.title.includes('accesibilidad'));
  assert.ok(data.h1.includes('accesibilidad'));
  assert.ok(data.ogTitle.includes('accesibilidad'));
  assert.ok(data.twitter.includes('accesibilidad'));
  assert.ok(data.robots.includes('index'));
});
console.log('accesibilidad-seo-parity: PASS');
