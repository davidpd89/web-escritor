import assert from 'node:assert/strict';
import fs from 'node:fs/promises';

const html = await fs.readFile(new URL('../gracias-suscripcion/index.html', import.meta.url), 'utf8');
const expected = 'https://davidportodiaz.com/gracias-suscripcion/';
function tag(pattern) {
  const value = html.match(pattern)?.[1];
  assert.ok(value, `Falta metadato ${pattern}`);
  return value;
}
const canonical = tag(/<link\s+rel="canonical"\s+href="([^"]+)"/i);
const og = tag(/<meta\s+property="og:url"\s+content="([^"]+)"/i);
const robots = tag(/<meta\s+name="robots"\s+content="([^"]+)"/i);
assert.equal(canonical, expected);
assert.equal(og, expected);
assert.ok(robots.split(',').map(s => s.trim()).includes('noindex'));
const blocks = [...html.matchAll(/<script\s+type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/gi)];
assert.ok(blocks.length);
const nodes = blocks.flatMap(m => {
  const obj = JSON.parse(m[1]);
  return obj['@graph'] ?? [obj];
});
const pages = nodes.filter(n => n['@type'] === 'WebPage');
assert.equal(pages.length, 1);
assert.equal(pages[0]['@id'], expected);
assert.equal(pages[0].url, expected);
const crumbs = pages[0].breadcrumb?.itemListElement;
assert.ok(Array.isArray(crumbs) && crumbs.length >= 2);
assert.equal(crumbs.at(-1).item, expected);
assert.deepEqual(crumbs.map(c => c.position), crumbs.map((_, i) => i + 1));
console.log('gracias-suscripcion SEO parity: PASS');
