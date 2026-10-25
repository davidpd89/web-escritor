import assert from 'node:assert/strict';

const BASE = (process.env.SITE_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const ROUTES = ['/', '/autor.html', '/prensa.html', '/libros/', '/herramientas/', '/cuaderno/', '/mapa-del-sitio/'];
const jobs = Array.from({length: 3}, () => ROUTES).flat();
const failures = [];
let next = 0;

async function worker() {
  while (next < jobs.length) {
    const route = jobs[next++];
    try {
      const response = await fetch(new URL(route, BASE), {signal: AbortSignal.timeout(15000)});
      const html = await response.text();
      assert.equal(response.status, 200, `${route}: HTTP ${response.status}`);
      assert.match(response.headers.get('content-type') || '', /text\/html/i, `${route}: Content-Type incorrecto`);
      assert.ok(html.length > 500, `${route}: respuesta vacía o truncada (${html.length} bytes)`);
      assert.match(html, /<title\b[^>]*>[^<]+<\/title>/i, `${route}: falta título HTML`);
      assert.match(html, /<body\b/i, `${route}: falta body`);
      assert.match(html, /<\/html\s*>/i, `${route}: documento incompleto`);
    } catch (error) {
      failures.push(`${route}: ${error.message}`);
    }
  }
}

await Promise.all(Array.from({length: 8}, worker));
assert.deepEqual(failures, [], failures.join('\n'));
console.log(`PASS: ${jobs.length} documentos HTML servidos correctamente con concurrencia 8`);
