import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const pages=await Promise.all(['privacidad.html','gracias-suscripcion/index.html'].map(p=>fs.readFile(new URL('../'+p,import.meta.url),'utf8')));
const essential=['v1-fonts.css','v1-tokens.css','v1-base.css','v1-shell.css','v1-components.css'];
for(const [i,html] of pages.entries()){
  assert.match(html,/<html\s+lang="es"/);
  assert.match(html,/name="viewport"\s+content="width=device-width, initial-scale=1\.0, viewport-fit=cover"/);
  for(const css of essential){
    assert.ok(html.includes('/assets/'+css),`Página ${i}: falta ${css}`);
  }
  assert.match(html,/class="skip-link"/);
  assert.match(html,/id="contenido"/);
}
console.log('newsletter legal shell typography: OK');