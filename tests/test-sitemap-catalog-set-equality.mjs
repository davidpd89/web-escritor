import assert from 'node:assert/strict';
import fs from 'node:fs';

const html=fs.readFileSync('mapa-del-sitio/index.html','utf8');
const registry=JSON.parse(fs.readFileSync('data/content-registry.json','utf8'));
const blocks=[...html.matchAll(/<details class="(?:directory-publishers|directory-reading-books)"><summary>([^<]+)<\/summary>([\s\S]*?)<\/details>/g)];
assert.equal(blocks.length,4);
const specs=[
  {prefix:'/editoriales/',label:'Ver las 150 editoriales'},
  {prefix:'/recomendaciones/libros/',label:'Ver las fichas de lectura'},
  {prefix:'/recomendaciones/autores/',label:'Ver autores del catálogo'},
  {prefix:'/recomendaciones/editoriales/',label:'Ver editoriales del catálogo'}
];
for(let i=0;i<specs.length;i++) {
  const {prefix,label}=specs[i];
  assert.equal(blocks[i][1],label);
  const actual=[...blocks[i][2].matchAll(/<a\s+href="([^"]+)"/g)].map(m=>m[1]);
  const expected=registry.entries.filter(e=>e.url.startsWith(prefix) && e.url!==prefix && (e.status ?? registry.defaults.status)==='public').map(e=>e.url);
  assert.equal(new Set(actual).size,actual.length,`${label}: rutas repetidas`);
  assert.deepEqual([...actual].sort(),[...expected].sort(),`${label}: diferencia exacta frente al registro`);
  console.log(`${label}: ${actual.length} rutas coherentes`);
}
console.log('PASS sitemap catalogue set equality');
