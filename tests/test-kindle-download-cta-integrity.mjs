import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const html = fs.readFileSync('las-manecillas-del-recuerdo/kindle/index.html', 'utf8');
const anchors = [...html.matchAll(/<a\b[^>]*data-sample-download="(epub|txt)"[^>]*>/g)].map(m => ({ tag: m[0], format: m[1] }));
assert.ok(anchors.length >= 3, 'Faltan CTA de descarga de la muestra');
const counts = { epub: 0, txt: 0 };
for (const { tag, format } of anchors) {
  const href = tag.match(/href="([^"]+)"/)?.[1];
  assert.ok(href?.startsWith('/assets/downloads/manecillas/'), `${format}: ruta de descarga no local`);
  assert.ok(tag.includes(' download'), `${format}: falta atributo download`);
  assert.equal(path.extname(href), `.${format}`, `${format}: extensión incorrecta`);
  const file = path.join('.', href);
  assert.ok(fs.existsSync(file), `${format}: archivo inexistente`);
  const bytes = fs.readFileSync(file);
  assert.ok(bytes.length > 500, `${format}: fichero vacío o incompleto`);
  if (format === 'epub') assert.equal(bytes.subarray(0, 2).toString(), 'PK', 'EPUB no es un contenedor ZIP');
  if (format === 'txt') {
    const text = new TextDecoder('utf-8', { fatal: true }).decode(bytes);
    assert.match(text, /Tomás contó las siete veces/);
  }
  counts[format]++;
}
assert.ok(counts.epub >= 2 && counts.txt >= 1, `Formatos accesibles incompletos: ${JSON.stringify(counts)}`);
console.log('OK: CTA y archivos de descarga verificados');
