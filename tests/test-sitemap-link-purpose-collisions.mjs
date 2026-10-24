import assert from 'node:assert/strict';
import fs from 'node:fs';

const html=fs.readFileSync('mapa-del-sitio/index.html','utf8');
const blocks=[...html.matchAll(/<details class="(?:directory-publishers|directory-reading-books)"><summary>([^<]+)<\/summary>([\s\S]*?)<\/details>/g)];
assert.equal(blocks.length,4);
const normalize=s=>s.replace(/<[^>]+>/g,'').replace(/&amp;/g,'&').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/\s+/g,' ').trim().toLocaleLowerCase('es');
for(const [,title,body] of blocks) {
  const names=new Map();
  const links=[...body.matchAll(/<a\s+href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/g)];
  assert(links.length>0);
  for(const [,href,content] of links) {
    const label=normalize(content);
    assert(label.length>=2,`${title}: etiqueta sin contenido`);
    assert(!/^(aqui|leer mas|ver mas|enlace|click aqui|pulsa aqui)$/u.test(label),`${title}: enlace genérico ${label}`);
    if(names.has(label)) assert.equal(names.get(label),href,`${title}: ${label} apunta a dos destinos`);
    names.set(label,href);
  }
}
console.log('PASS sitemap contextual link purposes');
