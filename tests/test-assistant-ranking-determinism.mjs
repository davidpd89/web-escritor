import assert from 'node:assert/strict';
import { rankLocalSources } from '../assets/assistant-core.mjs';

const sources = [
  { id: 'z', title: 'Zafiro', url: '/z/', visibility: 'public', priority: 2, keywords: ['reloj', 'misterio'] },
  { id: 'a', title: 'Álamo', url: '/a/', visibility: 'public', priority: 2, keywords: ['reloj', 'misterio'] },
  { id: 'm', title: 'Marfil', url: '/m/', visibility: 'public', priority: 2, keywords: ['reloj', 'misterio'] }
];
const ids = rows => rankLocalSources('reloj misterio', rows).map(s => s.id);
const reference = ids(sources);
assert.equal(reference.length, 3);
assert.deepEqual(ids([...sources].reverse()), reference, 'reverse order changed ranking');
assert.deepEqual(ids([sources[1], sources[2], sources[0]]), reference, 'rotation changed ranking');
const distractor = { id: 'noise', title: 'Una página ajena', url: '/noise/', visibility: 'public', priority: 1, keywords: ['astronomía'] };
assert.deepEqual(ids([distractor, ...sources]), reference, 'irrelevant insertion changed ranking');
const privateSource = { id: 'secret', title: 'Documento privado', url: '/secret/', visibility: 'private', priority: 0, keywords: ['reloj', 'misterio'] };
assert.deepEqual(ids([privateSource, ...sources]), reference, 'private source changed ranking');
console.log('PASS assistant stable local ranking');
