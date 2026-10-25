import assert from 'node:assert/strict';
import { normalizeWidgetPath, shouldMountAssistantWidget } from '../assets/assistant-widget-core.mjs';

for (const path of ['/asistente', '/asistente/', '/asistente/embed.html', '/asistente/?q=libros', '/asistente/#contenido', '//asistente///embed.html']) {
  assert.equal(shouldMountAssistantWidget(path), false, `Widget montado en ${path}`);
}

for (const path of ['/', '/autor.html', '/libros/', '/herramientas/', '/asistente-editorial/', '/asistentes/']) {
  assert.equal(shouldMountAssistantWidget(path), true, `Widget excluido en ${path}`);
}

assert.equal(normalizeWidgetPath('/libros///?q=1#inicio'), '/libros/');
assert.equal(normalizeWidgetPath('autor.html'), '/autor.html');
assert.equal(normalizeWidgetPath(''), '/');
console.log('assistant-widget-route-boundaries: OK');