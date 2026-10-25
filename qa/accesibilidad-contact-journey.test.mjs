import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const source = fs.readFileSync(path.join(root, 'accesibilidad/index.html'), 'utf8');

function extractContactLink(html) {
  const section = html.match(/<section\b[^>]*aria-labelledby="contacto"[^>]*>([\s\S]*?)<\/section>/i);
  assert.ok(section, 'Falta la sección de contacto');
  const link = section[1].match(/<a\b[^>]*href="([^"]+)"[^>]*>/i);
  assert.ok(link, 'La sección no ofrece un enlace de contacto');
  return link[1];
}

test('el recorrido de contacto termina en un mecanismo real', () => {
  const href = extractContactLink(source);
  if (/^mailto:/i.test(href)) {
    assert.match(href, /^mailto:[^\s@]+@[^\s@]+\.[^\s@]+/);
    return;
  }
  assert.ok(href.startsWith('/'), 'El destino debe ser interno o mailto');
  const url = new URL(href, 'https://davidportodiaz.com');
  const relative = decodeURIComponent(url.pathname).replace(/^\//, '');
  const file = path.join(root, relative.endsWith('/') ? relative + 'index.html' : relative);
  assert.ok(fs.existsSync(file), `Destino inexistente: ${href}`);
  const target = fs.readFileSync(file, 'utf8');
  if (url.hash) {
    const id = decodeURIComponent(url.hash.slice(1));
    assert.ok(target.includes(`id="${id}"`) || target.includes(`id='${id}'`), `Fragmento inexistente: ${url.hash}`);
  }
  assert.match(target, /mailto:|<form\b|data-email-reveal|href="https:\/\/[^\"]+\/contact/i, 'El destino no contiene un mecanismo reconocible de contacto');
});