import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';

const PORT = 18761;
const origin = process.env.QA_ORIGIN || `http://127.0.0.1:${PORT}`;
const server = process.env.QA_ORIGIN ? null : spawn('python3', ['-m', 'http.server', String(PORT), '--bind', '127.0.0.1'], { stdio: 'ignore' });
const routes = ['/', '/libros/', '/privacidad.html'];

async function ready() {
  for (let i = 0; i < 40; i++) {
    try { if ((await fetch(origin + '/')).ok) return; } catch {}
    await delay(100);
  }
  throw new Error('Servidor local no disponible');
}

try {
  await ready();
  const jobs = Array.from({ length: 36 }, (_, i) => routes[i % routes.length]);
  const results = await Promise.all(jobs.map(async route => {
    const response = await fetch(origin + route, { signal: AbortSignal.timeout(10000) });
    return { route, status: response.status, type: response.headers.get('content-type'), html: await response.text() };
  }));
  for (const result of results) {
    const prefix = `${result.route}: HTTP ${result.status}, bytes ${Buffer.byteLength(result.html)}`;
    assert.equal(result.status, 200, prefix);
    assert.match(result.type || '', /text\/html/i, prefix);
    assert.ok(result.html.length > 1000, prefix);
    assert.match(result.html, /<!doctype html>/i, prefix);
    assert.match(result.html, /<title>[^<]+<\/title>/i, prefix);
    assert.match(result.html, /<\/html>/i, prefix);
  }
  console.log(`OK: ${results.length} respuestas HTML de conversión`);
} finally {
  server?.kill();
}