import assert from 'node:assert/strict';
import fs from 'node:fs';

const html=fs.readFileSync('mapa-del-sitio/index.html','utf8');
assert.match(html,/<html\s+lang="es"/);
const main=html.match(/<main\b[^>]*>([\s\S]*?)<\/main>/)?.[1];
assert(main);
const rawLabels=[...main.matchAll(/<a\b[^>]*href="[^"]+"[^>]*>([\s\S]*?)<\/a>/g)].map(m=>m[1]);
assert(rawLabels.length>=300);
const allowedNamed=new Set(['amp','quot','apos','lt','gt','nbsp','laquo','raquo','hellip','mdash','ndash','copy','reg']);
for(const original of rawLabels) {
  const text=original.replace(/<[^>]*>/g,'').trim();
  assert(text.length>0,'etiqueta vacía');
  assert(!text.includes('\uFFFD'),`carácter de sustitución: ${text}`);
  assert(!/[\u200B-\u200D\uFEFF\u0000-\u0008\u000E-\u001F]/u.test(text),`control invisible: ${text}`);
  const withoutEntities=text.replace(/&(#\d+|#x[\da-fA-F]+|[a-zA-Z][a-zA-Z0-9]+);/g,(_,entity)=>{
    if(!entity.startsWith('#')) assert(allowedNamed.has(entity),`entidad no reconocida: ${entity}`);
    return 'X';
  });
  assert(!/&(?:#|[a-zA-Z])[a-zA-Z0-9#]*;/u.test(withoutEntities),`entidad residual: ${text}`);
  assert.equal(text.normalize('NFC'),text,`etiqueta no normalizada: ${text}`);
}
console.log(`PASS sitemap linguistic labels: ${rawLabels.length}`);
