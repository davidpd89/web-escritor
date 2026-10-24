import assert from 'node:assert/strict';
import fs from 'node:fs';

const html = fs.readFileSync('cuaderno/feria-libro-madrid-2026-samuel-entre-mundos/index.html', 'utf8');
const body = html.match(/<div class="article-prose"[^>]*>([\s\S]*?)<\/div>\s*<aside class="article-folio"/)?.[1] || html;
const figures = [...body.matchAll(/<figure(?:\s[^>]*)?>([\s\S]*?)<\/figure>/g)].map(m => m[1]);
assert.ok(figures.length >= 5, `Faltan fotografías documentales: ${figures.length}`);
const captions = new Set();
const alts = new Set();
const strip = s => s.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
for (const [index, figure] of figures.entries()) {
  const images = [...figure.matchAll(/<img\b[^>]*>/g)];
  assert.equal(images.length, 1, `Figura ${index + 1}: debe contener una fotografía`);
  const alt = images[0][0].match(/alt="([^"]+)"/)?.[1]?.trim();
  const caption = strip(figure.match(/<figcaption>([\s\S]*?)<\/figcaption>/)?.[1] || '');
  assert.ok(alt?.length >= 25, `Figura ${index + 1}: alt poco informativo`);
  assert.ok(caption.length >= 12, `Figura ${index + 1}: pie de foto vacío`);
  assert.ok(!captions.has(caption), `Figura ${index + 1}: pie duplicado`);
  assert.ok(!alts.has(alt), `Figura ${index + 1}: alt duplicado`);
  captions.add(caption);
  alts.add(alt);
}
console.log(`OK: ${figures.length} fotografías con descripción y pie`);
