import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
for(const [path,expected] of [['privacidad.html','https://davidportodiaz.com/privacidad.html'],['gracias-suscripcion/index.html','https://davidportodiaz.com/gracias-suscripcion/']]){
  const html=await fs.readFile(new URL('../'+path,import.meta.url),'utf8');
  const canonical=html.match(/<link\s+rel="canonical"\s+href="([^"]+)"/i)?.[1];
  assert.equal(canonical,expected,`${path}: canonical incorrecto`);
  assert.match(html,/<meta\s+name="robots"\s+content="noindex, follow"/i);
  const blocks=[...html.matchAll(/<script\s+type="application\/ld\+json"\s*>([\s\S]*?)<\/script>/gi)].map(m=>JSON.parse(m[1]));
  assert.ok(blocks.length,`${path}: falta JSON-LD`);
  const nodes=blocks.flatMap(b=>b['@graph']||[b]);
  const page=nodes.find(n=>n['@type']==='WebPage');
  assert.ok(page,`${path}: falta WebPage`);
  assert.equal(page.url,expected);
  assert.equal(page['@id'],expected);
  assert.equal(page.inLanguage,'es');
}
console.log('newsletter legal SEO parity: OK');