import assert from 'node:assert/strict';
import fs from 'node:fs';

const html = fs.readFileSync('universo/noveris/index.html', 'utf8');
const graph = JSON.parse(html.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/)?.[1] || '{}');
const nodes = graph['@graph'] || [graph];
const glossary = nodes.find(node => node['@type'] === 'DefinedTermSet');
assert.ok(glossary, 'Falta DefinedTermSet');
const terms = glossary.hasDefinedTerm;
assert.ok(Array.isArray(terms) && terms.length >= 5, 'Glosario incompleto');
const main = html.match(/<main\b[\s\S]*?<\/main>/)?.[0] || '';
const visible = main.replace(/<script[\s\S]*?<\/script>/g, '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ');
const names = new Set();
for (const term of terms) {
  assert.equal(term['@type'], 'DefinedTerm');
  assert.ok(term.name?.trim(), 'Término sin nombre');
  assert.ok(term.description?.trim().length >= 35, `${term.name}: definición demasiado breve`);
  assert.ok(!names.has(term.name.toLowerCase()), `${term.name}: término duplicado`);
  assert.ok(visible.toLowerCase().includes(term.name.toLowerCase()), `${term.name}: no aparece en el cuerpo`);
  names.add(term.name.toLowerCase());
  if (term['@id']?.startsWith('https://davidportodiaz.com/universo/noveris/#')) {
    const id = new URL(term['@id']).hash.slice(1);
    assert.ok(html.includes(`id="${id}"`), `${term.name}: @id sin ancla #${id}`);
  }
}
console.log(`OK: ${terms.length} términos estructurados comprobados`);
