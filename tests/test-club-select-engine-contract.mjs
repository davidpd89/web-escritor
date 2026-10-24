import assert from 'node:assert/strict';
import fs from 'node:fs';
import { buildSession } from '../assets/club-session-engine.js';

const html = fs.readFileSync('clubes-de-lectura/preparar-sesion/index.html', 'utf8');
const engine = fs.readFileSync('assets/club-session-engine.js', 'utf8');

function options(id) {
  const block = html.match(new RegExp(`<select[^>]*id="${id}"[^>]*>([\\s\\S]*?)<\\/select>`));
  assert.ok(block, `${id}: selector no encontrado`);
  return [...block[1].matchAll(/<option\s+value="([^"]+)"/g)].map(match => match[1]);
}

for (const genre of options('club-genre').filter(x => x !== 'general')) {
  assert.match(engine, new RegExp(`^\\s*${genre}:\\s*\\[`, 'm'), `Género sin banco: ${genre}`);
}
for (const kind of options('club-kind')) {
  assert.equal(buildSession({ kind }).kind, kind, `Tipo sin soporte: ${kind}`);
}
for (const tone of options('club-tone')) {
  assert.equal(buildSession({ tone }).tone, tone, `Tono sin soporte: ${tone}`);
  assert.match(engine, new RegExp(`^\\s*${tone}:\\s*\\[`, 'm'), `Tono sin actividades: ${tone}`);
}
for (const duration of options('club-duration')) {
  assert.equal(buildSession({ duration }).duration, Number(duration), `Duración sin soporte: ${duration}`);
}
for (const scope of options('club-scope')) {
  assert.equal(buildSession({ scope }).scope, scope, `Alcance sin soporte: ${scope}`);
}
console.log('test-club-select-engine-contract: OK');