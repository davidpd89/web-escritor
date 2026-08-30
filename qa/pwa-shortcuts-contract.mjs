import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(fileURLToPath(new URL('..', import.meta.url)));
const manifest = JSON.parse(readFileSync(join(ROOT, 'manifest.json'), 'utf8'));

const expectedUrls = [
  '/las-manecillas-del-recuerdo/',
  '/libros/',
  '/cuaderno/',
  '/prensa.html'
];

assert(Array.isArray(manifest.shortcuts), 'manifest.shortcuts must be an array');
assert.equal(manifest.shortcuts.length, expectedUrls.length, 'Canonical PWA shortcut count changed');

const urls = manifest.shortcuts.map((shortcut) => shortcut?.url);
assert.equal(new Set(urls).size, urls.length, 'PWA shortcut URLs must be unique');
assert.deepEqual([...urls].sort(), [...expectedUrls].sort(), 'Canonical PWA shortcut destinations changed');

for (const shortcut of manifest.shortcuts) {
  for (const field of ['name', 'short_name', 'url', 'description']) {
    assert.equal(typeof shortcut?.[field], 'string', `Shortcut ${shortcut?.url || '(unknown)'} missing ${field}`);
    assert(shortcut[field].trim().length > 0, `Shortcut ${shortcut.url} has empty ${field}`);
  }

  assert(shortcut.url.startsWith('/'), `Shortcut must be same-origin/root-relative: ${shortcut.url}`);
  assert(!shortcut.url.startsWith('//'), `Shortcut must not be protocol-relative: ${shortcut.url}`);

  const relative = shortcut.url.replace(/^\//, '');
  const target = shortcut.url.endsWith('/')
    ? join(ROOT, relative, 'index.html')
    : join(ROOT, relative);
  assert(existsSync(target), `Shortcut target missing from repository: ${shortcut.url}`);
}

console.log(`PWA shortcut contract OK: ${manifest.shortcuts.length} canonical destinations`);
