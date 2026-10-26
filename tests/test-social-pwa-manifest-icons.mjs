import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const root = new URL('../', import.meta.url);
const html = fs.readFileSync(new URL('redes-sociales/index.html', root), 'utf8');
const worker = fs.readFileSync(new URL('service-worker.js', root), 'utf8');
const origin = 'https://davidportodiaz.com';

const context = vm.createContext({
  URL, Request, Response, Set, console,
  self: {location: {origin}, addEventListener() {}}
});
vm.runInContext(worker, context);
const shell = Array.from(vm.runInContext('APP_SHELL', context));

function localFile(pathname) {
  assert.ok(pathname.startsWith('/') && !pathname.includes('..'), `Recurso PWA no local: ${pathname}`);
  return new URL(pathname.slice(1), root);
}

test('/redes-sociales/: manifiesto e iconos disponibles en el shell offline', () => {
  const match = html.match(/<link\b[^>]*rel="manifest"[^>]*href="([^"]+)"/);
  assert.ok(match, '/redes-sociales/: falta el manifiesto');
  const manifestPath = new URL(match[1], origin).pathname;
  assert.ok(shell.includes(manifestPath), `${manifestPath}: manifiesto fuera de APP_SHELL`);
  const manifest = JSON.parse(fs.readFileSync(localFile(manifestPath), 'utf8'));
  assert.ok(Array.isArray(manifest.icons) && manifest.icons.length > 0, `${manifestPath}: sin iconos`);
  for (const icon of manifest.icons) {
    const pathname = new URL(icon.src, origin).pathname;
    assert.ok(shell.includes(pathname), `${pathname}: icono ausente del shell offline`);
    const bytes = fs.readFileSync(localFile(pathname));
    assert.ok(bytes.length >= 24, `${pathname}: imagen vacía o truncada`);
    assert.equal(bytes.subarray(0, 8).toString('hex'), '89504e470d0a1a0a', `${pathname}: firma PNG incorrecta`);
    const width = bytes.readUInt32BE(16);
    const height = bytes.readUInt32BE(20);
    assert.ok(width > 0 && height > 0, `${pathname}: dimensiones inválidas`);
    assert.ok(icon.sizes.split(/\s+/).includes(`${width}x${height}`), `${pathname}: dimensiones ${width}x${height} distintas del manifiesto`);
  }
});