import assert from 'node:assert/strict';
import { slugify, sanitizeFilename, validatePressKitModel, buildTextFiles, sha256Hex } from '../assets/kit-prensa-core.js';

const model = {
  authorName: 'Ana Ejemplo', contactEmail: 'prensa@example.test', website: 'https://example.test',
  bioShort: 'Autora de narrativa contemporánea.', bioLong: 'Biografía larga.', bookTitle: 'La casa de prueba',
  publisher: 'Editorial Ejemplo', isbn: '9781234567890', publicationDate: '2026-09-03', price: '16 €',
  purchaseUrl: 'https://example.test/libro', bookDescription: 'Texto controlado para prensa.',
  interviewTopics: 'Memoria\nEscritura', assetPermission: 'contact_only',
};

assert.equal(validatePressKitModel(model).length, 0);
for (const [patch, expected] of [
  [{ authorName: '' }, 'nombre del autor'],
  [{ contactEmail: '' }, 'email de prensa'],
  [{ contactEmail: 'x' }, 'email de prensa'],
  [{ bookTitle: '' }, 'título del libro'],
  [{ bookDescription: '' }, 'descripción/sinopsis'],
  [{ website: 'http://example.test' }, 'web'],
  [{ purchaseUrl: 'javascript:alert(1)' }, 'enlace oficial'],
  [{ publicationDate: '2026-02-30' }, 'fecha de publicación'],
]) {
  assert.ok(validatePressKitModel({ ...model, ...patch }).some(x => x.toLowerCase().includes(expected)), `no detectó ${expected}`);
}

assert.equal(slugify('María López'), 'maria-lopez');
assert.equal(sanitizeFilename('Foto María FINAL.JPG'), 'foto-maria-final.jpg');
assert.equal(sanitizeFilename('../../archivo.txt'), 'archivo.txt');
assert.equal(sanitizeFilename('\"><svg onload=alert(1)>.PNG'), 'svg-onload-alert-1.png');
assert.equal(sanitizeFilename('portada ñandú.webp'), 'portada-nandu.webp');

// Windows reserved device names (item from the 2026-09 audit round): a
// file whose sanitized stem is exactly one of these fails to extract, or
// extracts to the wrong thing, on Windows regardless of extension -- must
// never survive sanitization unmodified.
for (const [input, expected] of [
  ['CON.jpg', 'con-file.jpg'],
  ['NUL.png', 'nul-file.png'],
  ['con', 'con-file'],
  ['lpt1.pdf', 'lpt1-file.pdf'],
  ['COM3.docx', 'com3-file.docx'],
  ['aux.txt', 'aux-file.txt'],
  ['constable.jpg', 'constable.jpg'], // must not false-positive on a name that merely starts with a reserved prefix
]) {
  assert.equal(sanitizeFilename(input), expected, `reserved-name handling for ${input}`);
}

const built = buildTextFiles(model, [{ role: 'author' }, { role: 'cover' }]);
for (const key of ['README.txt', 'datos/autor.json', 'datos/libro.json', 'textos/biografia-corta.txt', 'textos/sinopsis.txt', 'PERMISOS_ASSETS.txt']) {
  assert.ok(built.files[key], `missing ${key}`);
}
assert.ok(!built.checklist.some(x => x.includes('fotografía')));
assert.equal(JSON.parse(built.files['datos/autor.json']).name, 'Ana Ejemplo');
assert.equal(JSON.parse(built.files['datos/libro.json']).title, 'La casa de prueba');
assert.match(built.files['PERMISOS_ASSETS.txt'], /contactar previamente/i);

const hash = await sha256Hex(new TextEncoder().encode('abc'));
assert.equal(hash, 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad');

console.log('tests/test-kit-prensa-core: OK');
