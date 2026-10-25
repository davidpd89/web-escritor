import assert from 'node:assert/strict';
import fs from 'node:fs';

const BASE = (process.env.SITE_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const documents = ['index.html', '404.html'];
const assets = new Set();

for (const file of documents) {
  const html = fs.readFileSync(file, 'utf8');
  for (const match of html.matchAll(/\b(?:src|href)=["']([^"']+)["']/gi)) {
    const url = new URL(match[1], BASE);
    if (url.origin !== BASE || !/\.(?:css|js|mjs)$/i.test(url.pathname)) continue;
    if (fs.existsSync(url.pathname.slice(1))) assets.add(url.pathname + url.search);
  }
}

assert.ok(assets.size >= 5, `Inventario CSS/JS insuficiente: ${assets.size}`);
const jobs = [...assets].flatMap(asset => [asset, asset]);
let next = 0;
const failures = [];

async function worker() {
  while (next < jobs.length) {
    const asset = jobs[next++];
    try {
      const response = await fetch(new URL(asset, BASE), {signal: AbortSignal.timeout(15000)});
      const bytes = Buffer.from(await response.arrayBuffer());
      const mime = response.headers.get('content-type') || '';
      assert.equal(response.status, 200, `${asset}: HTTP ${response.status}`);
      assert.ok(bytes.length > 0, `${asset}: recurso vacío`);
      assert.doesNotMatch(mime, /text\/html/i, `${asset}: HTML servido como recurso`);
      if (/\.css(?:\?|$)/i.test(asset)) assert.match(mime, /text\/css/i, `${asset}: MIME ${mime}`);
      else assert.match(mime, /javascript|ecmascript/i, `${asset}: MIME ${mime}`);
    } catch (error) {
      failures.push(`${asset}: ${error.message}`);
    }
  }
}

await Promise.all(Array.from({length: 8}, worker));
assert.deepEqual(failures, [], failures.join('\n'));
console.log(`PASS: ${jobs.length} peticiones CSS/JS concurrentes`);
