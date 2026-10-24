import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const html=fs.readFileSync('mapa-del-sitio/index.html','utf8');
const blocks=[...html.matchAll(/<details class="(?:directory-publishers|directory-reading-books)"><summary>[^<]+<\/summary>([\s\S]*?)<\/details>/g)];
assert.equal(blocks.length,4);
const decode=s=>s.replace(/&amp;/g,'&').replace(/&quot;/g,'"').replace(/&nbsp;/g,' ').replace(/&#(\d+);/g,(_,n)=>String.fromCodePoint(Number(n)));
const normalize=s=>decode(s.replace(/<[^>]+>/g,'')).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('es').replace(/[^a-z0-9]+/g,' ').trim();
let checked=0;
for(let group=0;group<blocks.length;group++) {
  const anchors=[...blocks[group][1].matchAll(/<a\s+href="([^"]+)">([\s\S]*?)<\/a>/g)];
  assert(anchors.length>0);
  for(const [,href,labelHtml] of anchors) {
    const clean=new URL(href,'https://davidportodiaz.com');
    assert.equal(clean.hostname,'davidportodiaz.com');
    const file=path.join(clean.pathname.slice(1),'index.html');
    assert(fs.existsSync(file),`${href}: destino inexistente`);
    const target=fs.readFileSync(file,'utf8');
    const h1=target.match(/<h1\b[^>]*>([\s\S]*?)<\/h1>/i);
    assert(h1,`${href}: sin H1`);
    const label=group===1 ? labelHtml.split(/\s+[—–]\s+/)[0] : labelHtml;
    const wanted=normalize(label);
    const actual=normalize(h1[1]);
    assert(wanted.length>=2,`${href}: etiqueta vacía`);
    assert(actual.includes(wanted) || wanted.includes(actual),`${href}: ${JSON.stringify(wanted)} no coincide con H1 ${JSON.stringify(actual)}`);
    checked++;
  }
}
assert(checked>=300,`solo ${checked} destinos revisados`);
console.log(`PASS sitemap destination intent: ${checked} enlaces`);
