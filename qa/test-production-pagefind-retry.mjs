import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';

// Regresión del audit de Pagefind en producción: durante un deploy, Pages puede servir
// pagefind.js de una versión y trozos del índice de otra (o un 503), y la búsqueda falla con
// «invalid gzip data». En main eso tumbaba «Post-deploy deep audit» aunque el índice nuevo
// estuviera bien segundos después (en local el índice corrupto da cero resultados). Aquí se corrompen las primeras respuestas del índice y el
// audit debe recuperarse recargando; si el índice sigue roto, debe seguir fallando.
const root = process.cwd();
const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json' };

async function run(corruptions) {
  let left = corruptions;
  const server = createServer(async (req, res) => {
    let path = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    if (/^\/pagefind\/(index|fragment)\//.test(path) && left > 0) {
      left--;
      res.writeHead(200, { 'content-type': 'application/octet-stream' });
      return res.end(Buffer.from('not gzip at all, rotated index'));
    }
    if (path.endsWith('/')) path += 'index.html';
    const file = normalize(join(root, path));
    if (!file.startsWith(root)) { res.writeHead(403); return res.end(); }
    try {
      const body = await readFile(file);
      res.writeHead(200, { 'content-type': types[extname(file)] || 'application/octet-stream', 'cache-control': 'no-store' });
      res.end(body);
    } catch { res.writeHead(404); res.end(); }
  });
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = `http://127.0.0.1:${server.address().port}`;
  try {
    return await new Promise(resolve => {
      const child = spawn(process.execPath, ['qa/production-pagefind-search.mjs'], {
        env: { ...process.env, SITE_BASE_URL: base, EXPECTED_RELEASE_SHA: '', PAGEFIND_RETRY_DELAY_MS: '50' },
        stdio: ['ignore', 'pipe', 'pipe'],
      });
      let out = '';
      child.stdout.on('data', d => { out += d; });
      child.stderr.on('data', d => { out += d; });
      child.on('close', code => resolve({ code, out }));
    });
  } finally {
    server.close();
  }
}

const transient = await run(2);
assert.equal(transient.code, 0, `el audit no se recupera de un índice rotado transitorio:\n${transient.out.slice(-1500)}`);
assert.match(transient.out, /PASS production Pagefind/);

const broken = await run(Infinity);
assert.notEqual(broken.code, 0, 'un índice roto de forma persistente debe seguir fallando');
assert.match(broken.out, /attempt 3: .*(invalid gzip data|returned zero results)/i, 'el fallo persistente debe agotar los intentos y conservar la causa');
console.log('PASS production Pagefind retry: transient rotated index recovers, persistent corruption still fails');
