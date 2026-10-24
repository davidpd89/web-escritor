import assert from 'node:assert/strict';
import { rankLocalSources } from '../assets/assistant-core.mjs';

const sources = [
  { id: 'magic', title: 'Magia y fantasía', url: '/magia/', visibility: 'public', priority: 1, keywords: ['fantasía'] },
  { id: 'book', title: 'El reloj', url: '/reloj/', visibility: 'public', priority: 1, keywords: ['memoria'] },
  { id: 'private', title: 'Magia secreta', url: '/secreto/', visibility: 'private', priority: 1, keywords: ['magia'] },
  { id: 'external', title: 'Magia externa', url: '//evil.example/', visibility: 'public', priority: 1, keywords: ['magia'] },
];
const ids = (q, items) => rankLocalSources(q, items).map(x => x.id);

for (const query of ['fantasía', 'FANTASÍA', 'fantasia', 'Fantasía']) {
  assert.deepEqual(ids(query, sources), ids('fantasia', sources), `Variante: ${query}`);
}
for (const query of ['magia', 'memoria', 'reloj']) {
  assert.deepEqual(ids(query, sources), ids(query, [...sources].reverse()), `Orden variable: ${query}`);
  assert(!ids(query, sources).includes('private'));
  assert(!ids(query, sources).includes('external'));
}
assert.deepEqual(ids('palabra inexistente xyz', sources), []);
console.log('assistant-ranking-metamorphic: OK');
