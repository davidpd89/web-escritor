import assert from 'node:assert/strict';
import { isValidAssistantResponse, formatCitationMarkers } from '../assets/assistant-core.mjs';

const author = { id: 'author', title: 'Autor', url: '/autor.html' };
const work = { id: 'work', title: 'Libro', url: '/libros/' };
const response = (answer, sources, abstained = false) => ({
  protocol_version: 1, ok: true, answer, sources, abstained,
});

assert.equal(isValidAssistantResponse(response('Biografía [author]', [author])), true);
assert.equal(isValidAssistantResponse(response('Biografía [author]', [author, work])), false,
  'Una fuente no citada no debe mostrarse como evidencia de la respuesta');
assert.equal(isValidAssistantResponse(response('Dato [work]', [author])), false);
assert.equal(isValidAssistantResponse(response('Dato [author]', [author, author])), false);
assert.equal(isValidAssistantResponse(response('Dato sin fuente', [author])), false);

const text = formatCitationMarkers('A [work]. B [author]. C [work].', [author, work]);
assert.equal(text, 'A [2]. B [1]. C [2].');
assert.equal((text.match(/\[2\]/g) || []).length, 2);
console.log('assistant-citation-traceability: OK');
