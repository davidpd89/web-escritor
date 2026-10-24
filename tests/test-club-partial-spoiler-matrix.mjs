import assert from 'node:assert/strict';
import { buildSession } from '../assets/club-session-engine.js';

const genres = ['general', 'fantasy', 'scifi', 'mystery', 'romance', 'historical', 'contemporary', 'horror', 'memoir'];
const ending = /\b(final|desenlace|terminar|terminaste|acabó|cierre)\b|después de terminar|llegar al final|principio y el final|último capítulo|tras acabar/i;
let checked = 0;

for (const kind of ['fiction', 'nonfiction']) {
  for (const genre of genres) {
    for (const tone of ['social', 'balanced', 'deep']) {
      for (let variant = 0; variant < 12; variant++) {
        const session = buildSession({
          title: 'Lectura en progreso',
          kind, genre, tone,
          scope: 'partial',
          duration: 90,
          tokens: 'memoria, familia, identidad, confianza'
        }, variant);
        assert.equal(session.scope, 'partial');
        for (const question of [...session.opening, ...session.questions]) {
          assert.ok(!ending.test(question), `${kind}/${genre}/${tone}/${variant}: posible spoiler: ${question}`);
          checked++;
        }
      }
    }
  }
}
assert.ok(checked > 5000, `Matriz demasiado pequeña: ${checked}`);
console.log(`test-club-partial-spoiler-matrix: OK (${checked} preguntas)`);