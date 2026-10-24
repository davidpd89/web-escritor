import assert from 'node:assert/strict';
import fs from 'node:fs';

const samuel = fs.readFileSync('fragmento/index.html', 'utf8');
const manecillas = fs.readFileSync('las-manecillas-del-recuerdo/fragmentos/index.html', 'utf8');
const samuelArticle = samuel.match(/<article class="fragment-reading fragment-text" data-nosnippet>([\s\S]*?)<\/article>/);
assert.ok(samuelArticle, 'Samuel: prosa sin contenedor data-nosnippet');
assert.ok((samuelArticle[1].match(/<p\b/g) || []).length >= 15, 'Samuel: muestra literaria incompleta');
const excerpts = [...manecillas.matchAll(/<div class="excerpt-field" data-nosnippet>([\s\S]*?)<\/div>/g)];
assert.equal(excerpts.length, 3, 'Manecillas: los tres fragmentos deben tener data-nosnippet');
for (const [file, passages] of [[samuel, [samuelArticle[1]]], [manecillas, excerpts.map(m => m[1])]]) {
  const jsonld = [...file.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)].map(m => m[1]).join('\n');
  for (const passage of passages) {
    const text = passage.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
    assert.ok(text.length > 120, 'Pasaje inesperadamente vacío');
    const opening = text.slice(0, 80);
    assert.ok(!jsonld.includes(opening), `Prosa literaria copiada dentro de JSON-LD: ${opening}`);
  }
}
console.log('OK: aislamiento literario de Samuel y Manecillas');
