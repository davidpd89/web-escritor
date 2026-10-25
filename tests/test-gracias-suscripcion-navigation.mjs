import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const html = await fs.readFile(path.join(root, 'gracias-suscripcion/index.html'), 'utf8');
const main = html.match(/<main\b[\s\S]*?<\/main>/i)?.[0];
assert.ok(main);
const expected = ['/fragmento/', '/', '/las-manecillas-del-recuerdo/'];
for (const route of expected) {
  assert.ok([...main.matchAll(/href="([^"]+)"/g)].some(m => m[1] === route), `Falta enlace ${route}`);
  const relative = route === '/' ? 'index.html' : `${route.slice(1)}index.html`;
  const file = path.resolve(root, relative);
  assert.ok(file.startsWith(root + path.sep));
  const target = await fs.readFile(file, 'utf8');
  assert.match(target, /<!doctype html>/i);
  assert.match(target, /<title\b[^>]*>[^<]+<\/title>/i);
  assert.match(target, /<main\b/i);
}
console.log('gracias-suscripcion navigation: PASS');
