import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';

const ROOT = process.cwd();
const ROUTES = [
  {
    route: 'las-manecillas-del-recuerdo/fragmentos/index.html',
    label: 'Descargar el capítulo 1.1 completo'
  }
];

function attributes(tag) {
  const result = new Map();
  const pattern = /([\w-]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'))?/g;
  for (const match of tag.matchAll(pattern)) {
    result.set(match[1].toLowerCase(), match[2] ?? match[3] ?? '');
  }
  return result;
}

function findAction(html, label) {
  const anchors = [...html.matchAll(/<a\b([^>]*)>([\s\S]*?)<\/a>/gi)];
  const matches = anchors.filter(([, , body]) =>
    body.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim() === label
  );
  assert.equal(matches.length, 1, `Debe existir una única acción: ${label}`);
  return attributes(matches[0][1]);
}

for (const { route, label } of ROUTES) {
  test(`${route}: la descarga anunciada entrega un archivo real`, () => {
    const html = fs.readFileSync(path.join(ROOT, route), 'utf8');
    const action = findAction(html, label);
    const href = action.get('href');

    assert.ok(href, 'La acción necesita un destino');
    assert.ok(action.has('download'), 'Una acción que promete descargar debe ofrecer descarga directa');
    assert.match(href, /^\/assets\/downloads\/manecillas\/[^?#]+\.(epub|txt)$/i,
      'El destino debe ser un archivo de muestra publicado, no otra página HTML');

    const relative = decodeURIComponent(new URL(href, 'https://davidportodiaz.com').pathname).slice(1);
    const absolute = path.resolve(ROOT, relative);
    const downloads = path.resolve(ROOT, 'assets/downloads/manecillas');
    assert.ok(absolute.startsWith(downloads + path.sep), 'El archivo debe pertenecer al directorio público de muestras');
    assert.ok(fs.existsSync(absolute), `No existe el archivo descargable: ${relative}`);
    assert.ok(fs.statSync(absolute).size > 0, 'El archivo descargable está vacío');
  });
}
