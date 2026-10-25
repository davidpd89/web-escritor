import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import test from 'node:test';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const html = readFileSync(resolve(root, 'al-otro-lado/index.html'), 'utf8');

function extractBook() {
  const blocks = [...html.matchAll(/<script\b[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi)];
  assert.ok(blocks.length, 'La página publicada debe contener JSON-LD');
  const nodes = blocks.flatMap((match) => {
    const data = JSON.parse(match[1]);
    return Array.isArray(data['@graph']) ? data['@graph'] : [data];
  });
  const book = nodes.find((node) => {
    const types = Array.isArray(node['@type']) ? node['@type'] : [node['@type']];
    return types.includes('Book') && node.name === 'Al otro lado';
  });
  assert.ok(book, 'Falta el nodo Book de la antología');
  return book;
}

test('la antología declara los dos formatos que anuncia públicamente', () => {
  assert.match(html, /El libro se editó en 2026 en papel y en formato digital/i,
    'La prueba debe seguir vinculada a la afirmación editorial publicada');

  const book = extractBook();
  const formats = Array.isArray(book.bookFormat)
    ? book.bookFormat
    : book.bookFormat ? [book.bookFormat] : [];

  assert.ok(formats.includes('https://schema.org/EBook'),
    'El formato digital anunciado debe figurar en Book.bookFormat');
  assert.ok(formats.includes('https://schema.org/Paperback') ||
            formats.includes('https://schema.org/Hardcover'),
    'La edición en papel anunciada debe figurar en Book.bookFormat');
});
