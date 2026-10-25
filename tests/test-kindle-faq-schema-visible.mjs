import assert from 'node:assert/strict';
import fs from 'node:fs';

const html = fs.readFileSync('las-manecillas-del-recuerdo/kindle/index.html', 'utf8');
const graph = JSON.parse(html.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/)?.[1] || '{}');
const nodes = graph['@graph'] || [graph];
const page = nodes.find(n => n['@type'] === 'WebPage');
const faq = page?.mainEntity?.['@type'] === 'FAQPage' ? page.mainEntity : nodes.find(n => n['@type'] === 'FAQPage');
assert.ok(faq, 'Falta FAQPage');
const start = html.indexOf('id="preguntas"');
assert.ok(start !== -1, 'Falta sección visible de preguntas');
const visible = html.slice(start, html.indexOf('</section>', start)).replace(/<[^>]*>/g, ' ').replace(/&[^;]+;/g, ' ').replace(/\s+/g, ' ').toLowerCase();
const clean = value => String(value || '').toLowerCase().replace(/[¿?¡!.,:;—–]/g, '').replace(/\s+/g, ' ').trim();
const comparable = clean(visible);
assert.ok(faq.mainEntity.length >= 3, 'Muy pocas preguntas estructuradas');
for (const question of faq.mainEntity) {
  assert.equal(question['@type'], 'Question');
  const name = clean(question.name);
  assert.ok(comparable.includes(name), `Pregunta estructurada no visible: ${question.name}`);
  assert.ok(question.acceptedAnswer?.text?.trim().length >= 15, `Respuesta vacía: ${name}`);
}
console.log('OK: preguntas FAQ contrastadas con el contenido visible');
