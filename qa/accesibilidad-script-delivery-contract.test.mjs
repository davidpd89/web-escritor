import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const html = fs.readFileSync(path.join(root, 'accesibilidad/index.html'), 'utf8');
const scripts = [...html.matchAll(/<script\b[^>]*>/gi)].map(m => m[0]);
const attr = (tag, name) => new RegExp('(?:^|\\s)' + name + '\\s*=\s*["\x27]([^"\x27]+)["\x27]', 'i').exec(tag)?.[1];
const has = (tag, name) => new RegExp('(?:^|\\s)' + name + '(?:\\s|=|>)', 'i').test(tag);

test('los scripts locales de accesibilidad son recursos JavaScript existentes', () => {
  const local = scripts.filter(tag => {
    const src = attr(tag, 'src');
    return src && new URL(src, 'https://davidportodiaz.com').origin === 'https://davidportodiaz.com';
  });
  assert.ok(local.length > 0, '/accesibilidad/: no se encuentran scripts locales');
  for (const tag of local) {
    const src = attr(tag, 'src');
    const url = new URL(src, 'https://davidportodiaz.com');
    assert.match(url.pathname, /\.(?:js|mjs)$/i, `/accesibilidad/: script con extensión inesperada ${src}`);
    const file = path.join(root, url.pathname.slice(1));
    assert.ok(fs.existsSync(file), `/accesibilidad/: script inexistente ${src}`);
    assert.ok(fs.statSync(file).size > 0, `/accesibilidad/: script vacío ${src}`);
  }
});

test('los scripts externos no bloquean el analizador HTML', () => {
  for (const tag of scripts) {
    const src = attr(tag, 'src');
    if (!src) continue;
    const type = (attr(tag, 'type') || '').toLowerCase();
    const nonBlocking = has(tag, 'defer') || has(tag, 'async') || type === 'module';
    assert.ok(nonBlocking, `/accesibilidad/: script externo bloqueante ${src}`);
  }
});

test('los bloques JSON-LD permanecen separados del JavaScript ejecutable', () => {
  const blocks = [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)];
  for (const block of blocks) {
    if ((attr(block[1], 'type') || '').toLowerCase() !== 'application/ld+json') continue;
    assert.ok(!attr(block[1], 'src'), '/accesibilidad/: JSON-LD no debe tener src ejecutable');
    assert.doesNotThrow(() => JSON.parse(block[2]), '/accesibilidad/: JSON-LD inválido');
  }
});