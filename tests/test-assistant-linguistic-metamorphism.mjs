import assert from 'node:assert/strict';
import { resolveLocalAnswer } from '../assets/assistant-local-knowledge.mjs';

const fixtures = [
  ['¿Qué es Noveris?', 'QUE ES NOVERIS'],
  ['¿Qué herramientas gratuitas hay?', 'que herramientas gratuitas hay'],
  ['¿Cómo puedo contactar con David?', 'COMO PUEDO CONTACTAR CON DAVID'],
  ['¿Qué concursos para escritores hay?', 'que concursos para escritores hay'],
  ['¿De qué trata Samuel entre mundos?', 'de que trata SAMUEL ENTRE MUNDOS'],
  ['¿Dónde puedo leer un fragmento gratis?', 'donde puedo leer un fragmento gratis']
];
for (const [base, variant] of fixtures) {
  const reference = resolveLocalAnswer(base, {});
  const changed = resolveLocalAnswer(variant, {});
  assert.ok(reference && changed, `unrecognized equivalent query: ${base}`);
  assert.equal(changed.intent, reference.intent, `intent drift: ${variant}`);
  assert.deepEqual(changed.sourceIds, reference.sourceIds, `source drift: ${variant}`);
  const spaced = resolveLocalAnswer(`  ${base.replace(/ /g, '   ')}  `, {});
  assert.equal(spaced?.intent, reference.intent, `whitespace drift: ${base}`);
  const decomposed = resolveLocalAnswer(base.normalize('NFD'), {});
  assert.equal(decomposed?.intent, reference.intent, `Unicode composition drift: ${base}`);
}
console.log(`PASS ${fixtures.length} assistant linguistic fixture groups`);
