import assert from 'node:assert/strict';
import { slugify, sanitizeFilename, validatePressKitModel, buildTextFiles, sha256Hex } from '../assets/kit-prensa-core.js';

const model = {
  authorName: 'María López', contactEmail: 'maria@example.com', website: 'https://maria.example/',
  bioShort: 'Autora de narrativa contemporánea.', bioLong: 'Biografía larga.', bookTitle: 'La casa azul',
  publisher: 'Editorial X', isbn: '9780000000000', publicationDate: '2026-09-03', price: '16 €',
  purchaseUrl: 'https://maria.example/libro', bookDescription: 'Una novela sobre memoria.',
  interviewTopics: 'Memoria\nEscritura', assetPermission: 'contact_only',
};

assert.equal(validatePressKitModel(model).length, 0);
assert.ok(validatePressKitModel({ ...model, contactEmail: 'x' }).length > 0);
assert.equal(slugify('María López'), 'maria-lopez');
assert.equal(sanitizeFilename('Foto María FINAL.JPG'), 'foto-maria-final.jpg');

const built = buildTextFiles(model, [{ role: 'author' }, { role: 'cover' }]);
for (const key of ['README.txt', 'datos/autor.json', 'datos/libro.json', 'textos/biografia-corta.txt', 'textos/sinopsis.txt', 'PERMISOS_ASSETS.txt']) {
  assert.ok(built.files[key], `missing ${key}`);
}
assert.ok(!built.checklist.some(x => x.includes('fotografía')));

const hash = await sha256Hex(new TextEncoder().encode('abc'));
assert.equal(hash, 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad');

console.log('tests/test-kit-prensa-core: OK');
