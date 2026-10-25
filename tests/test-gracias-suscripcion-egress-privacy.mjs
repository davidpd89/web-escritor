import assert from 'node:assert/strict';
import fs from 'node:fs/promises';

const html = await fs.readFile(new URL('../gracias-suscripcion/index.html', import.meta.url), 'utf8');
const main = html.match(/<main\b[\s\S]*?<\/main>/i)?.[0];
assert.ok(main, 'Falta el contenido principal');
const links = [...main.matchAll(/<a\b[^>]*\bhref=['"]([^'"]+)['"]/gi)].map(m => m[1]);
assert.ok(links.length >= 3, 'Deben existir alternativas de navegación');
for (const href of links) {
  const url = new URL(href, 'https://davidportodiaz.com');
  assert.equal(url.protocol, 'https:');
  assert.equal(url.origin, 'https://davidportodiaz.com');
  for (const key of url.searchParams.keys()) {
    assert.doesNotMatch(key, /email|token|contact|subscriber|hash|code|key/i);
  }
  assert.doesNotMatch(href, /[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i);
}
console.log('gracias-suscripcion egress privacy: PASS');
