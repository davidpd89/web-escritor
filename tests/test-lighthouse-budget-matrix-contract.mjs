import assert from 'node:assert/strict';
import fs from 'node:fs';

const config = JSON.parse(fs.readFileSync('lighthouserc.json', 'utf8'));
const urls = config.ci.collect.url;
const matrix = config.ci.assert.assertMatrix;
assert.ok(Array.isArray(urls) && urls.length >= 10);
assert.equal(new Set(urls).size, urls.length, 'Duplicate Lighthouse URLs');
assert.ok(config.ci.collect.numberOfRuns >= 3);

const families = [
  '/', '/ai/', '/libros/', '/herramientas/',
  '/asistente/', '/las-manecillas-del-recuerdo/'
];
for (const family of families) {
  assert.ok(urls.some(url => new URL(url).pathname.startsWith(family)), `Missing family: ${family}`);
}

for (const url of urls) {
  const matching = matrix.filter(rule => new RegExp(rule.matchingUrlPattern).test(url));
  assert.ok(matching.length > 0, `No assertion matrix for ${url}`);
  for (const rule of matching) {
    const assertions = rule.assertions;
    assert.ok(assertions['categories:accessibility'], `Accessibility missing for ${url}`);
    assert.notEqual(assertions['categories:accessibility'], 'off');
    assert.ok(assertions['cumulative-layout-shift'], `CLS missing for ${url}`);
    assert.notEqual(assertions['cumulative-layout-shift'], 'off');
    assert.ok(assertions['largest-contentful-paint'], `LCP missing for ${url}`);
    assert.ok(assertions['total-blocking-time'], `TBT missing for ${url}`);
  }
}
console.log(`PASS: Lighthouse matrix covers ${urls.length} URLs`);