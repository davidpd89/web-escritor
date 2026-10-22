// QA offline para el CTA de seguir autor: sin Amazon, red ni cookies.
// Ejecución pendiente: node --test tests/test-amazon-author-follow.mjs
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import test from 'node:test';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const files = [
  'autor.html',
  'libros/samuel-entre-mundos/index.html',
  'las-manecillas-del-recuerdo/index.html',
];
const canonical = 'https://www.amazon.es/stores/author/B0GZFP1JV3';
const read = path => readFileSync(resolve(root, path), 'utf8');

for (const file of files) {
  test('CTA visible correcto y no afiliado: ' + file, () => {
    const html = read(file);
    const anchors = [...html.matchAll(/<a\s+[^>]*class="[^"]*amazon-author-follow-link[^"]*"[^>]*>/g)].map(m => m[0]);
    assert.equal(anchors.length, 1, 'Debe haber solo un CTA en la página');
    assert.match(anchors[0], /href="https:\/\/www\.amazon\.es\/stores\/author\/B0GZFP1JV3"/);
    assert.match(anchors[0], /rel="noopener noreferrer"/);
    assert.doesNotMatch(anchors[0], /tag=|sponsored/);
    assert.match(html, />Seguir al autor en Amazon<\/a>/);
    assert.ok(html.includes(canonical), 'No cambiar destino oficial');
  });
}

test('taxonomía Author Follow explícita y sin compra', () => {
  const registry = JSON.parse(read('data/analytics-events.json'));
  const entry = registry.events.find(e => e.name === 'seguir-autor-amazon');
  assert.equal(entry?.action, 'author_follow_outbound');
  const js = read('script.js');
  assert.match(js, /link\.matches\("a\.amazon-author-follow-link\[href\]"\)/);
  assert.match(js, /_gcEvent\("seguir-autor-amazon",/);
  assert.match(js, /B0GZFP1JV3/);
  assert.match(js, /author\.pathname/);
  assert.doesNotMatch(js, /_gcEvent\("comprar-amazon", "Clic saliente: Seguir/);
});
