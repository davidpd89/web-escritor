import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const html=fs.readFileSync('mapa-del-sitio/index.html','utf8');
const blocks=[...html.matchAll(/<details class="(?:directory-publishers|directory-reading-books)"><summary>[^<]+<\/summary>([\s\S]*?)<\/details>/g)];
assert.equal(blocks.length,4);
let checked=0;
for(const block of blocks) {
  for(const [,href] of block[1].matchAll(/<a\b[^>]*href="([^"]+)"/g)) {
    const expected=new URL(href,'https://davidportodiaz.com').href;
    const parsed=new URL(expected);
    assert.equal(parsed.hostname,'davidportodiaz.com');
    const file=path.join(parsed.pathname.slice(1),'index.html');
    assert(fs.existsSync(file),`${href}: HTML inexistente`);
    const target=fs.readFileSync(file,'utf8');
    const canonical=target.match(/<link\b[^>]*rel="canonical"[^>]*href="([^"]+)"/i)?.[1] ?? target.match(/<link\b[^>]*href="([^"]+)"[^>]*rel="canonical"/i)?.[1];
    const og=target.match(/<meta\b[^>]*property="og:url"[^>]*content="([^"]+)"/i)?.[1] ?? target.match(/<meta\b[^>]*content="([^"]+)"[^>]*property="og:url"/i)?.[1];
    assert.equal(canonical,expected,`${href}: canonical distinto del enlace`);
    assert.equal(og,expected,`${href}: og:url distinto del enlace`);
    assert.match(target,/<title>[^<]{5,}<\/title>/i,`${href}: title vacío`);
    checked++;
  }
}
assert(checked>=300);
console.log(`PASS sitemap target metadata parity: ${checked} fichas`);
