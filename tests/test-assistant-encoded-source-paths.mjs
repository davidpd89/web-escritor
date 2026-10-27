import assert from 'node:assert/strict';
import { isSafeInternalPath, isValidAssistantResponse } from '../assets/assistant-core.mjs';

const accepted = ['/autor.html', '/libros/samuel-entre-mundos/', '/asistente/'];
const rejected = [
  '//evil.example/a',
  '/a/../secret',
  '/a/%2e%2e/secret',
  '/a/%2E%2E/secret',
  '/a/%252e%252e/secret',
  '/a/%5csecret',
  '/a/%255csecret',
  '/a/%2f%2fevil.example',
  '/a/%0d%0aLocation:evil.example',
];

for (const url of accepted) {
  assert.equal(isSafeInternalPath(url), true, `Ruta pública rechazada: ${url}`);
}
for (const url of rejected) {
  assert.equal(isSafeInternalPath(url), false, `Ruta ambigua aceptada: ${url}`);
  assert.equal(isValidAssistantResponse({
    protocol_version: 1, ok: true, answer: 'Fuente [author]',
    abstained: false, sources: [{ id: 'author', title: 'Autor', url }],
  }), false, `Respuesta con destino ambiguo aceptada: ${url}`);
}
console.log('assistant-encoded-source-paths: OK');
