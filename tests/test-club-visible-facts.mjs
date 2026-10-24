import assert from 'node:assert/strict';
import fs from 'node:fs';

const facts = JSON.parse(fs.readFileSync('editorial-facts.json', 'utf8')).books.samuelEntreMundos;
const html = [
  ['principal', fs.readFileSync('clubes-de-lectura/samuel-entre-mundos/index.html', 'utf8')],
  ['imprimible', fs.readFileSync('clubes-de-lectura/samuel-entre-mundos/guia-imprimible/index.html', 'utf8')]
];

for (const [name, source] of html) {
  const block = name === 'principal'
    ? source.match(/<section[^>]+id="ficha"[\s\S]*?<\/section>/)?.[0]
    : source.match(/<div class="meta-grid">[\s\S]*?<\/div>/)?.[0];
  assert.ok(block, `${name}: no se encuentra la ficha visible`);
  for (const [field, value] of [
    ['isbn', facts.isbn],
    ['publicationYear', facts.publicationYear],
    ['numberOfPages', facts.numberOfPages]
  ]) {
    assert.ok(block.includes(String(value)), `${name}: ${field} diverge de editorial-facts.json`);
  }
  assert.match(block, /Samuel entre mundos/);
  assert.match(block, /David Porto Díaz/);
  assert.match(block, /Libros Indie/);
}
console.log('test-club-visible-facts: OK');