import assert from 'node:assert/strict';
import fs from 'node:fs';

const html=fs.readFileSync('mapa-del-sitio/index.html','utf8');
const main=html.match(/<main\b[^>]*>([\s\S]*?)<\/main>/)?.[1];
assert(main,'main ausente');
const sections=[...main.matchAll(/<section class="directory-group"\s+id="([^"]+)"([^>]*)>([\s\S]*?)<\/section>/g)];
assert.equal(sections.length,7,'deben existir siete secciones');
const ids=new Set();
for(const section of sections) {
  const [,id,attrs,body]=section;
  assert(!ids.has(id),`sección duplicada ${id}`);
  ids.add(id);
  const heading=body.match(/<h2\b([^>]*)>([\s\S]*?)<\/h2>/);
  assert(heading,`${id}: falta H2`);
  assert(heading[2].replace(/<[^>]+>/g,'').trim(),`${id}: H2 vacío`);
  const labelledby=attrs.match(/\baria-labelledby="([^"]+)"/);
  assert(labelledby,`${id}: región sin aria-labelledby`);
  const headingId=heading[1].match(/\bid="([^"]+)"/);
  assert(headingId,`${id}: H2 sin id`);
  assert.equal(labelledby[1],headingId[1],`${id}: relación aria-labelledby incorrecta`);
}
console.log('PASS sitemap named region associations');
