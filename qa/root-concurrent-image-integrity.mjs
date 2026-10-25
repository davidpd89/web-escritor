import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';

const BASE = (process.env.SITE_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const images = new Set();
for (const file of ['index.html', '404.html']) {
  const html = fs.readFileSync(file, 'utf8');
  for (const match of html.matchAll(/\b(?:src|poster|href)=["']([^"']+)["']/gi)) {
    const url = new URL(match[1], BASE);
    if (url.origin === BASE && /\.(?:png|jpg|jpeg|webp|avif|svg|ico)$/i.test(url.pathname) && fs.existsSync(url.pathname.slice(1))) images.add(url.pathname);
  }
}
assert.ok(images.size > 0, 'No se encontraron imágenes locales en los documentos reales');
const jobs = [...images].flatMap(image => [image, image]);
const failures = [];
let next = 0;
const digest = bytes => crypto.createHash('sha256').update(bytes).digest('hex');

async function worker() {
  while (next < jobs.length) {
    const image = jobs[next++];
    try {
      const expected = fs.readFileSync(image.slice(1));
      const response = await fetch(new URL(image, BASE), {signal: AbortSignal.timeout(15000)});
      const actual = Buffer.from(await response.arrayBuffer());
      assert.equal(response.status, 200, `${image}: HTTP ${response.status}`);
      assert.ok(actual.length > 0, `${image}: imagen vacía`);
      assert.equal(actual.length, expected.length, `${image}: tamaño recibido ${actual.length}, esperado ${expected.length}`);
      assert.equal(digest(actual), digest(expected), `${image}: contenido binario distinto`);
      assert.doesNotMatch(response.headers.get('content-type') || '', /text\/html/i, `${image}: respuesta HTML inesperada`);
    } catch (error) {
      failures.push(`${image}: ${error.message}`);
    }
  }
}

await Promise.all(Array.from({length: 6}, worker));
assert.deepEqual(failures, [], failures.join('\n'));
console.log(`PASS: ${jobs.length} entregas binarias de imágenes concurrentes`);
