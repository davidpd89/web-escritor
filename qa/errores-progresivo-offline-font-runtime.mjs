import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createWorker } from './errores-progresivo-sw-fixture.mjs';

const root = resolve(fileURLToPath(new URL('..', import.meta.url)));
const html = readFileSync(resolve(root, 'offline.html'), 'utf8');
const sw = readFileSync(resolve(root, 'service-worker.js'), 'utf8');
const fonts = [...new Set([...html.matchAll(/src:\s*url\(["']?(\/assets\/fonts\/[^)'" ]+)/g)].map(m => m[1]))];
assert.ok(fonts.length > 0, 'offline.html: no se han descubierto fuentes locales');

const shellBlock = sw.match(/const APP_SHELL = \[([\s\S]*?)\];/);
assert.ok(shellBlock, 'service-worker.js: no se encuentra APP_SHELL');
const shell = new Set([...shellBlock[1].matchAll(/["'](\/[^"']+)["']/g)].map(m => m[1]));

for (const font of fonts) {
  assert.ok(existsSync(resolve(root, font.slice(1))), `offline.html: fuente inexistente ${font}`);
  assert.ok(shell.has(font), `offline.html: fuente ausente del precache ${font}`);
}

const worker = createWorker(async request => {
  const url = new URL(typeof request === 'string' ? request : request.url, 'https://qa.invalid');
  const pathname = url.pathname;
  const file = resolve(root, pathname.slice(1));
  if (!existsSync(file)) return new Response('Not found', { status: 404 });
  return new Response(readFileSync(file), {
    status: 200,
    headers: { 'Content-Type': pathname.endsWith('.woff2') ? 'font/woff2' : pathname.endsWith('.html') ? 'text/html' : 'application/octet-stream' }
  });
});

await worker.install();
worker.setNetwork(async () => { throw new TypeError('Failed to fetch'); });

for (const font of fonts) {
  const result = await worker.fetch(worker.request(font, { destination: 'font' }));
  assert.equal(result.response.status, 200, `offline.html: fuente no recuperable sin red ${font}`);
  const bytes = new Uint8Array(await result.response.arrayBuffer());
  assert.ok(bytes.length > 0, `offline.html: fuente recuperada vacía ${font}`);
}
console.log(`PASS: ${fonts.length} fuentes de offline.html recuperables sin red`);