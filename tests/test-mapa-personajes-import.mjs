// Importación del mapa de personajes: un JSON ajeno o incompatible se rechaza
// con motivo y nunca se convierte en un mapa vacío o recortado.
import assert from 'node:assert/strict';
import { normalizeProject, parseProject, serializeProject, ProjectImportError } from '../assets/mapa-personajes-core.js';

const rejects = (label, value) => {
  const text = typeof value === 'string' ? value : JSON.stringify(value);
  assert.throws(() => parseProject(text), error => error instanceof ProjectImportError && error.message.length > 0, label);
};

const ana = { id: 'ana', name: 'Ana' };
const bruno = { id: 'bruno', name: 'Bruno' };

rejects('JSON roto', '{malformed');
rejects('objeto ajeno', { unrelated: 'data' });
rejects('array', []);
rejects('null', null);
rejects('versión futura', { version: 999, characters: [ana], relations: [] });
rejects('personajes no es lista', { version: 1, characters: 'Ana' });
rejects('relaciones no es lista', { version: 1, characters: [ana], relations: {} });
rejects('personaje sin nombre', { version: 1, characters: [{ id: 'x' }] });
rejects('nombre no texto', { version: 1, characters: [{ name: 42 }] });
rejects('id repetido', { version: 1, characters: [ana, { id: 'ana', name: 'Otra Ana' }] });
rejects('referencia rota', { version: 1, characters: [ana], relations: [{ from: 'ana', to: 'nadie' }] });
rejects('autorrelación', { version: 1, characters: [ana], relations: [{ from: 'ana', to: 'ana' }] });
rejects('tipo desconocido', { version: 1, characters: [ana, bruno], relations: [{ from: 'ana', to: 'bruno', type: 'odio' }] });
rejects('etiqueta larga', { version: 1, characters: [ana, bruno], relations: [{ from: 'ana', to: 'bruno', label: 'x'.repeat(81) }] });
rejects('evolución larga', { version: 1, characters: [ana, bruno], relations: [{ from: 'ana', to: 'bruno', evolution: 'x'.repeat(241) }] });
rejects('relación duplicada', { version: 1, characters: [ana, bruno], relations: [{ from: 'ana', to: 'bruno', type: 'amistad' }, { from: 'bruno', to: 'ana', type: 'amistad' }] });
rejects('dirección no booleana', { version: 1, characters: [ana, bruno], relations: [{ from: 'ana', to: 'bruno', directed: 'sí' }] });
rejects('título no texto', { version: 1, title: 7, characters: [] });

// Mapa vacío legítimo y exportación anterior sin campo version.
assert.deepEqual(parseProject('{"version":1,"title":"","characters":[],"relations":[]}').characters, []);
assert.equal(parseProject(JSON.stringify({ characters: [{ name: 'Ana' }, { name: 'Bruno' }], relations: [{ from: 'ana', to: 'bruno', type: 'amistad' }] })).relations.length, 1);

// Exportar y reimportar conserva todo.
const project = normalizeProject({
  title: 'Saga',
  characters: [{ name: 'Ana', note: 'protagonista' }, { name: 'Bruno' }, { name: 'Clara' }],
  relations: [
    { from: 'ana', to: 'bruno', type: 'amistad', label: 'confianza', evolution: 'se rompe', directed: false },
    { from: 'ana', to: 'clara', type: 'mentoria', directed: true },
  ],
});
assert.deepEqual(parseProject(serializeProject(project)), project);

// Un texto que parece HTML se conserva como texto.
assert.equal(parseProject(JSON.stringify({ version: 1, characters: [{ name: '<img src=x onerror=alert(1)>' }] })).characters[0].name, '<img src=x onerror=alert(1)>');

console.log('tests/test-mapa-personajes-import: OK');
