import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const html = fs.readFileSync(path.join(root, 'accesibilidad/index.html'), 'utf8');
const manifest = JSON.parse(fs.readFileSync(path.join(root, 'manifest.json'), 'utf8'));
const signature = Buffer.from([137,80,78,71,13,10,26,10]);

test('la declaración enlaza el manifiesto público existente', () => {
  assert.match(html, /<link\b[^>]*rel="manifest"[^>]*href="\/manifest\.json"/i, '/accesibilidad/: falta el manifest.json');
  assert.ok(Array.isArray(manifest.icons) && manifest.icons.length > 0, '/manifest.json: no contiene iconos');
});

test('los iconos PNG del manifiesto tienen bytes, dimensiones y peso correctos', () => {
  for (const icon of manifest.icons) {
    assert.equal(icon.type, 'image/png', `/manifest.json: tipo de ${icon.src}`);
    const url = new URL(icon.src, 'https://davidportodiaz.com');
    assert.equal(url.origin, 'https://davidportodiaz.com', `/manifest.json: icono externo ${icon.src}`);
    const file = path.join(root, url.pathname.slice(1));
    assert.ok(fs.existsSync(file), `/manifest.json: icono inexistente ${icon.src}`);
    const data = fs.readFileSync(file);
    assert.ok(data.subarray(0, 8).equals(signature), `/manifest.json: ${icon.src} no es PNG`);
    assert.equal(data.toString('ascii', 12, 16), 'IHDR', `/manifest.json: ${icon.src} sin cabecera IHDR`);
    const width = data.readUInt32BE(16);
    const height = data.readUInt32BE(20);
    const declared = icon.sizes.split(/\s+/).map(s => s.split('x').map(Number));
    assert.ok(declared.some(([w,h]) => w === width && h === height), `/manifest.json: ${icon.src} declara ${icon.sizes} pero mide ${width}x${height}`);
    assert.ok(data.length <= 512 * 1024, `/manifest.json: ${icon.src} pesa ${data.length} bytes, límite 524288`);
  }
});