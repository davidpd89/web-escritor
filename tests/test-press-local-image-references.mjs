import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const root=process.cwd();
const page='prensa.html';
const html=fs.readFileSync(path.join(root,page),'utf8');
const tags=[...html.matchAll(/<img\b[^>]*>/gi)].map(m=>m[0]);
assert.ok(tags.length>=5,`${page}: faltan imágenes documentales esperadas`);
let checked=0;
for(const tag of tags){
  const raw=tag.match(/\bsrc=["']([^"']+)["']/i)?.[1];
  assert.ok(raw,`${page}: imagen sin src: ${tag.slice(0,100)}`);
  const url=new URL(raw,'https://davidportodiaz.com');
  if(url.origin!=='https://davidportodiaz.com')continue;
  const local=path.resolve(root,'.'+decodeURIComponent(url.pathname));
  assert.ok(local.startsWith(root+path.sep),`${page}: ruta fuera del repositorio: ${raw}`);
  assert.ok(fs.existsSync(local),`${page}: imagen inexistente: ${raw}`);
  assert.ok(fs.statSync(local).size>0,`${page}: imagen vacía: ${raw}`);
  checked++;
}
assert.ok(checked>=5,`${page}: solo se comprobaron ${checked} imágenes locales`);
console.log(`PASS: ${checked} imágenes locales de prensa verificadas`);