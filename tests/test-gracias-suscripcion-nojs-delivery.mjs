import assert from 'node:assert/strict';
import fs from 'node:fs/promises';

const thanks = await fs.readFile(new URL('../gracias-suscripcion/index.html', import.meta.url), 'utf8');
const fragment = await fs.readFile(new URL('../fragmento/index.html', import.meta.url), 'utf8');
const main = thanks.match(/<main\b[\s\S]*?<\/main>/i)?.[0];
assert.ok(main);
const links = [...main.matchAll(/<a\b([^>]*)>([\s\S]*?)<\/a>/gi)];
const chapter = links.find(m => /primer capítulo/i.test(m[2]));
assert.ok(chapter, 'No existe acceso directo al capítulo');
assert.match(chapter[1], /href="\/fragmento\/"/);
assert.doesNotMatch(chapter[1], /onclick\s*=|href="javascript:/i);
assert.doesNotMatch(main, /<form\b/i, 'La entrega no debe exigir un nuevo formulario');
assert.match(fragment, /<main\b/i);
assert.match(fragment, /Samuel entre mundos/i);
console.log('gracias-suscripcion nojs delivery: PASS');
