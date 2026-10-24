import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const html=fs.readFileSync('mapa-del-sitio/index.html','utf8');
const sections=[...html.matchAll(/<section class="directory-group" id="([^"]+)"[^>]*>([\s\S]*?)<\/section>/g)];
assert.equal(sections.length,7);
const intentionalMinimal=new Set(['/ai/','/clubes-de-lectura/samuel-entre-mundos/guia-imprimible/']);
let checked=0;
for(const [,section,body] of sections) {
  const urls=[...new Set([...body.matchAll(/<a\b[^>]*href="(\/[^"#?]+)(?:[?#][^"]*)?"/g)].map(m=>m[1]))].filter(url=>url!=='/mapa-del-sitio/' && !intentionalMinimal.has(url));
  assert(urls.length>0,`${section}: sin destinos`);
  const selected=[urls[0],urls[Math.floor(urls.length/2)],urls.at(-1)];
  for(const url of new Set(selected)) {
    const clean=url.replace(/^\//,'');
    const file=url==='/' ? 'index.html' : url.endsWith('/') ? path.join(clean,'index.html') : clean;
    assert(fs.existsSync(file),`${section}: ${url} inexistente`);
    const target=fs.readFileSync(file,'utf8');
    assert.match(target,/<header\b[^>]*class="site-header"/,`${section}: ${url} sin cabecera global`);
    assert.match(target,/<a\b[^>]*class="header-sitemap"[^>]*href="\/mapa-del-sitio\/"/,`${section}: ${url} no permite volver al mapa`);
    checked++;
  }
}
assert(checked>=14);
console.log(`PASS sitemap cross-family return: ${checked} destinos`);
