import assert from 'node:assert/strict';
import { assistantContextStarters } from '../assets/assistant-widget-core.mjs';

const paths = ['/', '/autor.html', '/las-manecillas-del-recuerdo/', '/las-manecillas-del-recuerdo/fragmentos/', '/libros/samuel-entre-mundos/', '/universo/noveris/', '/fragmento/', '/herramientas/', '/editoriales/', '/convocatorias-escritores/', '/prensa.html', '/eventos.html', '/premios.html'];

for (const path of paths) {
  const starters = assistantContextStarters(path);
  assert.ok(Array.isArray(starters), `${path}: resultado no iterable`);
  assert.equal(starters.length, 3, `${path}: número de sugerencias`);
  const normalized = starters.map(value => {
    assert.equal(typeof value, 'string');
    assert.equal(value, value.trim(), `${path}: espacios exteriores`);
    assert.ok(value.length >= 10 && value.length <= 500, `${path}: longitud incorrecta`);
    assert.doesNotMatch(value, /[\u0000-\u001f\u007f]/);
    return value.normalize('NFC').toLocaleLowerCase('es');
  });
  assert.equal(new Set(normalized).size, 3, `${path}: preguntas duplicadas`);
}

assert.match(assistantContextStarters('/universo/noveris/').join(' '), /Noveris/i);
assert.match(assistantContextStarters('/editoriales/').join(' '), /editoriales/i);
assert.match(assistantContextStarters('/prensa.html').join(' '), /prensa|contactar|eventos/i);
console.log('assistant-context-starters-integrity: OK');