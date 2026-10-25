import assert from 'node:assert/strict';
import { resolveLocalAnswer } from '../assets/assistant-local-knowledge.mjs';
import { ASSISTANT_SOURCE_REGISTRY } from '../assets/assistant-source-registry.js';

const registry = new Map(ASSISTANT_SOURCE_REGISTRY.map(source => [source.id, source]));
assert.equal(registry.size, ASSISTANT_SOURCE_REGISTRY.length, 'Identificadores duplicados en el registro');

const queries = [
  '¿De qué trata Las manecillas del recuerdo?',
  '¿Cuándo se publicó Las manecillas del recuerdo?',
  '¿Dónde puedo comprar Las manecillas del recuerdo?',
  '¿Dónde leo un fragmento?',
  '¿De qué trata Samuel entre mundos?',
  '¿Qué es Noveris?',
  '¿Dónde puedo enviar un manuscrito?',
  '¿Qué concursos para escritores hay?',
  '¿Qué herramientas gratuitas hay?',
  '¿Dónde encuentro el kit de prensa?',
  '¿Cómo puedo contactar con David?',
  '¿Qué eventos hay?',
  '¿Qué premios tiene?',
  '¿Qué libros ha publicado David?',
  '¿Qué puedo encontrar en esta web?'
];

for (const query of queries) {
  const answer = resolveLocalAnswer(query);
  assert.ok(answer, `Sin respuesta local: ${query}`);
  assert.equal(typeof answer.answer, 'string');
  assert.ok(answer.answer.trim().length > 0);
  const ids = answer.sourceIds || [];
  assert.ok(Array.isArray(ids));
  assert.equal(new Set(ids).size, ids.length, `Fuentes duplicadas: ${query}`);
  for (const id of ids) {
    assert.ok(registry.has(id), `Fuente desconocida ${id}: ${query}`);
    assert.equal(registry.get(id).visibility, 'public', `Fuente no pública: ${id}`);
  }
}
console.log('assistant-local-answer-source-integrity: OK');