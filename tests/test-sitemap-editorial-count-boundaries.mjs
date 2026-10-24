import assert from 'node:assert/strict';
import fs from 'node:fs';

const html=fs.readFileSync('mapa-del-sitio/index.html','utf8');
const publishers=JSON.parse(fs.readFileSync('editoriales/editoriales-data.json','utf8')).publishers;
function inspect(markup) {
  const block=markup.match(/<details class="directory-publishers"><summary>([^<]+)<\/summary>([\s\S]*?)<\/details>/);
  assert(block,'desplegable editorial ausente');
  const numbers=[...block[1].matchAll(/\d+/g)];
  assert.equal(numbers.length,1,'el resumen debe presentar una única cardinalidad');
  const announced=Number(numbers[0][0]);
  const links=[...block[2].matchAll(/<a\s+href="\/editoriales\/[^"/]+\/"/g)];
  assert.equal(announced,links.length,'el resumen anuncia una cantidad incorrecta');
  assert.equal(links.length,publishers.length,'el HTML difiere de los datos editoriales');
  return announced;
}
const count=inspect(html);
assert(count>0);
for (const delta of [-1,1]) {
  const mutated=html.replace(`Ver las ${count} editoriales`,`Ver las ${count+delta} editoriales`);
  assert.notEqual(mutated,html);
  assert.throws(()=>inspect(mutated),/cantidad incorrecta/);
}
console.log('PASS sitemap editorial count boundary mutations');
